import os
import gc
import shutil
import requests
import rioxarray
import rasterio
import numpy as np
import pandas as pd
import geopandas as gpd
from tqdm import tqdm
from tempfile import TemporaryDirectory
from datetime import datetime, timedelta
from diskcache import Cache
from boto3 import client
from botocore.config import Config
from botocore.exceptions import ClientError

from .db.InvalidImage import InvalidImage
from .util import convert_to_cog_rio, fill_geotiff_stack


class GLAD():
  '''
    https://glad.umd.edu/ard/home
  '''

  _cache = Cache(__name__)
  _data_cache = '.geomap'
  _base_url = "https://glad.umd.edu"
  _interval_id_url = f'{_base_url}/users/Potapov/ARD/16d_intervals.xlsx'
  _tile_geojson_url = f'{_base_url}/users/Potapov/ARD/Global_ARD_tiles.zip'
  _days_before_update = 20
  _s3_root_path = 'geomap/glad_ard2'
  _s3_public_url = os.environ['PUBLIC_S3_URL']
  _auth = ('glad', 'ardpas')
  _valid_image_pixels = 0.7
  
  def __init__(self):
    self.get_interval_table()
    self.get_tile_geojson()
    self._s3_bucket = os.environ['S3_URL'].split('/')[-1]
    self._s3 = client('s3', aws_access_key_id=os.environ['S3_ACCESS_KEY'],
                      aws_secret_access_key=os.environ['S3_SECRET_KEY'],
                      endpoint_url=os.environ['S3_URL'][:-len(self._s3_bucket)-1],
                      config=Config(signature_version = 'v4'))

  def get_interval_table(self):
    '''
      Get the 16 day interval table from GLAD.
    '''
    if not 'interval_table' in self._cache:
      print('Downloading interval table from GLAD...')
      # Interval ID table
      self._interval_table = pd.read_excel(self._interval_id_url, sheet_name='16d interval ID', 
                                            header=1, index_col='Year')
      # Date lookup table
      dates = pd.read_excel(self._interval_id_url, sheet_name='16d interval dates',
                                            index_col='Interval ID')['end Date'].to_list()
      
      # Use the lookup table to create a date table
      self._interval_dates = self._interval_table.copy().astype('str')
      for index, _ in self._interval_dates.iterrows():
        self._interval_dates.loc[index] = dates.copy()
      self._interval_dates = self._interval_dates.astype('datetime64[ns]')
      for index, _ in self._interval_dates.iterrows():
        self._interval_dates.loc[index] = self._interval_dates.loc[index].apply(lambda x: datetime(index, x.month, x.day))

      self._cache.set('interval_table', self._interval_table)
      self._cache.set('interval_dates', self._interval_dates)

    else:
      self._interval_table = self._cache.get('interval_table')
      self._interval_dates = self._cache.get('interval_dates')
                                            
    return self._interval_table, self._interval_dates
  
  def get_tile_geojson(self):
    '''
      Get the tiles geojson from GLAD.
    '''
    if not 'tile_geojson' in self._cache:
      print('Downloading tile geojson from GLAD...')
      self._tile_geojson = gpd.read_file(self._tile_geojson_url)

      self._cache.set('tile_geojson', self._tile_geojson)

    else:
      self._tile_geojson = self._cache.get('tile_geojson')
                                            
    return self._tile_geojson
  
  def get_valid_ids(self, tile_id: str = None):
    '''
    Get the valid interval IDs from GLAD which are before the current date minus `_days_before_update`.

    Parameters
    ----------
    - tile_id str: Tile ID in the format '054W_03S'. If provided then invalid IDs from db will be filtered out.
                   Invalid ID could be corrupted image or lots of cloud etc.
    '''
    interval_table, interval_dates = self.get_interval_table()

    today = datetime.now() - timedelta(days=self._days_before_update)

    interval_table = interval_table[interval_dates < today]
    ids = interval_table.to_numpy().flatten()
    ids = ids[~(np.isnan(ids))].astype(int).tolist()
    
    if tile_id is not None:
      # Filter out invalid IDs
      q = InvalidImage.select(InvalidImage.interval_id).where(InvalidImage.tile_id == tile_id)
      invalid_ids = [r.interval_id for r in q]
      ids = [id for id in ids if id not in invalid_ids]

    return ids
  
  def get_image_base_url(self):
    return f'{self._s3_public_url}/{self._s3_root_path}'
  
  def get_image(self, tile_id: str, interval_id: int, retry: bool = False):
    '''
      Get the image for a Tile ID and Interval ID.

      Parameters
      ----------
      - tile_id: str - Tile ID in the format '054W_03S'
      - interval_id: int - Interval ID
      - retry: bool optional -  Retry processing if previously failed
    '''
    lat = tile_id.split('_')[1]
    s3_key = f'{self._s3_root_path}/{tile_id}/{interval_id}/raw.tif'

    interval_table, interval_dates = self.get_interval_table()
    idx = np.where(interval_table.to_numpy().flatten() == interval_id)[0][0]
    date = interval_dates.to_numpy().flatten()[idx]

    # Corrupted or cloudy image
    q = InvalidImage.select().where(InvalidImage.tile_id == tile_id, 
                                    InvalidImage.interval_id == interval_id)
    if len(q) > 0:
      if retry:
        q[0].delete_instance()
      else:
        raise Exception(f'Image {tile_id}:{interval_id} in invalid. {q[0].reason}')

    try:
      self._s3.get_object(Bucket=self._s3_bucket, Key=s3_key)
    
    except ClientError as e:
      error_code = e.response['Error']['Code']
      if error_code != 'NoSuchKey':
        raise e
      
      print(f'Image {tile_id}:{interval_id} not found in S3 ({s3_key}). Downloading from GLAD...')
      url = f'{self._base_url}/dataset/glad_ard2/{lat}/{tile_id}/{interval_id}.tif'
      
      # Download the image
      print(f'Downloading {url} ...')
      with TemporaryDirectory() as tdir:
        r = requests.get(url, auth=self._auth, stream=True)
        total_size = int(r.headers.get("content-length", 0))
        tmp_file_tif = os.path.join(tdir, 'temp.tif')
        with tqdm(total=total_size, unit="B", unit_scale=True, mininterval=10) as progress_bar:
          with open(tmp_file_tif, 'wb') as f:
            for bits in r.iter_content(chunk_size=8192):
              f.write(bits)
              progress_bar.update(len(bits))

        # Check for valid image
        invalid_image_reason = ''

        try:
          valid_pixel_percentage = 0
          with rasterio.open(tmp_file_tif, 'r+') as dataset:
            # Add a mask where band 8 is value 1 or 15
            # https://glad.umd.edu/Potapov/ARD/ARD_manual_v1.1.pdf pg 21
            qf = dataset.read(8)  # Read band 8
            mask = np.logical_or(qf == 1, qf == 15) 
            valid_pixel_percentage = mask.sum() / mask.size
            if valid_pixel_percentage < self._valid_image_pixels:
              raise Exception(f'Valid pixels in image are below threshold: {valid_pixel_percentage}')
            else:
              print(f'Valid pixels in image are above threshold: {valid_pixel_percentage}')
            dataset.nodata = 0
            for i in range(1, dataset.count + 1):
              band = dataset.read(i)
              band = np.where(mask, band, 0)
              dataset.write(band, i)

          tmp_file_cog = tmp_file_tif.replace('.tif', '.cog.tif')
          convert_to_cog_rio(tmp_file_tif, tmp_file_cog)

          # Upload to S3
          print(f'Uploading {tile_id}:{interval_id} to S3 ({s3_key}).')
          self._s3.upload_file(tmp_file_cog, self._s3_bucket, s3_key)
          print(f'Image {tile_id}:{interval_id} uploaded to S3.')

        except Exception as e:
          invalid_image_reason = str(e) 
          print(f'Error in processing image - {invalid_image_reason}')
          InvalidImage.create(tile_id=tile_id, interval_id=interval_id, 
                              reason=invalid_image_reason, valid_pixel_percentage=valid_pixel_percentage)
          raise e
        
        finally:
          gc.collect()


    # Generate a URL for the S3 object
    url = f'{self._s3_public_url}/{s3_key}'
    
    ds = rioxarray.open_rasterio(url, masked=True)
    ds['band'] = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'temp', 'qf']
    ds = ds.assign_coords(date=date)
    ds.attrs['url'] = url
    return ds
  
  def process_images_rgba(self, tile_id: str):
    '''
      Process the rgba images for a Tile ID.
      This involves extracting the RGB bands and running forward fill and back fill 
      on the stack to impute missing values.
    '''
    ids = self.list_images(tile_id)

    print(f'Processing RGBA images for Tile ID {tile_id}...')
    with TemporaryDirectory() as tdir:
      # Download stack of images
      for interval_id in tqdm(ids):
        s3_key = f'{self._s3_root_path}/{tile_id}/{interval_id}/raw.tif'
        raw_tif = os.path.join(tdir, f'{interval_id}-raw.tif')
        rgba_tif = os.path.join(tdir, f'{interval_id}-rgba.tif')
        
        print(f'Downloading {s3_key} to {raw_tif}...')
        self._s3.download_file(Bucket=self._s3_bucket, Key=s3_key, Filename=raw_tif)

        print(f'Extracting RGB bands...')
        with rasterio.open(raw_tif, mode='r') as src:
          rgba = src.read([3, 2, 1, 8])
          for i in range(3):
            rgba[i] = (rgba[i] - rgba[i].min()) / (rgba[i].max() - rgba[i].min()) * 255
          rgba = rgba.astype(np.uint8)
    
          qf = src.read(8)
          mask = np.logical_or(qf == 1, qf == 15) 
          rgba[3] = np.where(mask, 255, 0)
    
          new_meta = src.meta.copy()
          new_meta['count'] = 4
          new_meta['dtype'] = 'uint8'

          with rasterio.open(rgba_tif, 'w', **new_meta) as dst:
            dst.write(rgba)
          
          os.remove(raw_tif)

        del rgba, qf, mask, new_meta
        gc.collect()

      print(f'\nStacking and running ffill and bfill...')
      rgba_tifs = [os.path.join(tdir, f'{interval_id}-rgba.tif') for interval_id in ids]
      filled_tifs = [os.path.join(tdir, f'{interval_id}-filled.tif') for interval_id in ids]
      fill_geotiff_stack(rgba_tifs, filled_tifs, block_size=500, last_band_mask=True, no_data_value=0)

      for rgba_tif in rgba_tifs:
        os.remove(rgba_tif)

      # Convert to COGS and upload to S3
      for interval_id in tqdm(ids):
        s3_key = f'{self._s3_root_path}/{tile_id}/{interval_id}/rgba.tif'
        filled_tif = os.path.join(tdir, f'{interval_id}-filled.tif')
        tmp_file_cog = filled_tif.replace('.tif', '.cog.tif')
        convert_to_cog_rio(filled_tif, tmp_file_cog, add_mask=False)
        os.remove(filled_tif)
        
        # Upload to S3
        print(f'Uploading {tile_id}:{interval_id} to S3 ({s3_key}).')
        self._s3.upload_file(tmp_file_cog, self._s3_bucket, s3_key)
        print(f'Image {tile_id}:{interval_id} uploaded to S3.')
        os.remove(tmp_file_cog)

        gc.collect()

  def get_image_rgba(self, tile_id: str, interval_id: int):
    '''
      Get the image for a Tile ID and Interval ID.

      Parameters
      ----------
      - tile_id: str - Tile ID in the format '054W_03S'
      - interval_id: int - Interval ID
    '''
    s3_key = f'{self._s3_root_path}/{tile_id}/{interval_id}/rgba.tif'

    interval_table, interval_dates = self.get_interval_table()
    idx = np.where(interval_table.to_numpy().flatten() == interval_id)[0][0]
    date = interval_dates.to_numpy().flatten()[idx]

    # Generate a URL for the S3 object
    url = f'{self._s3_public_url}/{s3_key}'
    
    ds = rioxarray.open_rasterio(url)
    ds['band'] = ['red', 'green', 'blue', 'alpha']
    ds = ds.assign_coords(date=date)
    ds.attrs['url'] = url
    return ds
  
  def list_images(self, tile_id: str):
    prefix = f'{self._s3_root_path}/{tile_id}/'
    ids = self._s3.list_objects_v2(Bucket=self._s3_bucket, Prefix=prefix, Delimiter='/')['CommonPrefixes']
    ids = sorted([int(id['Prefix'].replace(prefix, '').split('/')[0]) for id in ids])
    return ids
  
  def list_tiles(self, full: bool = False):
    prefix = f'{self._s3_root_path}/'
    tiles = self._s3.list_objects_v2(Bucket=self._s3_bucket, Prefix=prefix, Delimiter='/')['CommonPrefixes']
    tiles = sorted([tile['Prefix'].replace(prefix, '').split('/')[0] for tile in tiles])

    if full:
      interval_table, interval_dates = self.get_interval_table()
      interval_table = interval_table.to_numpy().flatten()
      interval_dates = interval_dates.to_numpy().flatten()

      tiles = {tile: self.list_images(tile) for tile in tiles}
      for tile in tiles:
        tiles[tile] = [{'ID': id, 'Date': pd.Timestamp(interval_dates[np.where(interval_table == id)[0][0]])} 
                       for id in tiles[tile]]

    return tiles
  
  def delete_image(self, tile_id: str, interval_id: int):
    '''
    Delete the image for a Tile ID and Interval ID.

    Parameters
    ----------
    - tile_id str: Tile ID in the format '054W_03S'
    - interval_id int: Interval ID
    '''
    s3_key = f'{self._s3_root_path}/{tile_id}/{interval_id}/'
    
    try:
      keys = self._s3.list_objects_v2(Bucket=self._s3_bucket, Prefix=s3_key)['Contents']
      keys = {'Objects': [{'Key': key['Key']} for key in keys]}
      self._s3.delete_objects(Bucket=self._s3_bucket, Delete=keys)
    
    except Exception as e:
      pass

  def cache_clear(self):
    shutil.rmtree(self._data_cache, ignore_errors=True)