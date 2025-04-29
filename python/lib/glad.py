import os
import requests
import xarray as xr
import numpy as np
import pandas as pd
from tqdm import tqdm
from tempfile import NamedTemporaryFile
from datetime import datetime, timedelta
from diskcache import Cache
from boto3 import client
from botocore.exceptions import ClientError

from .db.InvalidImage import InvalidImage


class GLAD():
  '''
  https://glad.umd.edu/ard/home
  '''

  _cache = Cache(__name__)
  _data_cache = '.geomap'
  _base_url = "https://glad.umd.edu/"
  _interval_id_url = f'{_base_url}/users/Potapov/ARD/16d_intervals.xlsx'
  _days_before_update = 20
  _s3_root_path = 'geomap/glad_ard2'
  _auth = ('glad', 'ardpas')
  
  def __init__(self):
    self.get_interval_table()
    self._s3_bucket = os.environ['S3_URL'].split('/')[-1]
    self._s3 = client('s3', aws_access_key_id=os.environ['S3_ACCESS_KEY'],
                      aws_secret_access_key=os.environ['S3_SECRET_KEY'],
                      endpoint_url=os.environ['S3_URL'][:-len(self._s3_bucket)-1])

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
      print('Loading interval table from cache...')
      self._interval_table = self._cache.get('interval_table')
      self._interval_dates = self._cache.get('interval_dates')
                                            
    return self._interval_table, self._interval_dates
  
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
  
  def get_download_urls_for_tile(self, tile_id: str):
    '''
    Get the valid download URLs for a Tile ID.

    Parameters
    ----------
    - tile_id str: Tile ID in the format '054W_03S'
    '''
    ids = self.get_valid_ids()
    lat = tile_id.split('_')[1]

    urls = []
    for id in ids:
      url = f'{self._base_url}/dataset/glad_ard2/{lat}/{tile_id}/{id}.tif'
      urls.append(url)
    return urls
  
  def get_image(self, tile_id: str, interval_id: int):
    '''
    Get the image for a Tile ID and Interval ID.

    Parameters
    ----------
    - tile_id str: Tile ID in the format '054W_03S'
    - interval_id int: Interval ID
    '''
    lat = tile_id.split('_')[1]
    s3_key = f'{self._s3_root_path}/{tile_id}/raw/{interval_id}.tif'

    try:
      self._s3.get_object(Bucket=self._s3_bucket, Key=s3_key)
    
    except ClientError as e:
      error_code = e.response['Error']['Code']
      if error_code != 'NoSuchKey':
        raise e
      print(f'Image {tile_id}:{interval_id} not found in S3 ({s3_key}). Downloading from GLAD...')
      url = f'{self._base_url}/dataset/glad_ard2/{lat}/{tile_id}/{interval_id}.tif'
      
      # Download the image
      print(f'Downloading {url}...')
      with NamedTemporaryFile() as tmp_file:
        r = requests.get(url, auth=self._auth, stream=True)
        total_size = int(r.headers.get("content-length", 0))
        with tqdm(total=total_size, unit="B", unit_scale=True, mininterval=10) as progress_bar:
          for bits in r.iter_content(chunk_size=8192):
            tmp_file.write(bits)
            progress_bar.update(len(bits))
      
        # Upload to S3
        print(f'Uploading {tile_id}:{interval_id} to S3 ({s3_key}).')
        self._s3.upload_file(tmp_file.name, self._s3_bucket, s3_key)
        print(f'Image {tile_id}:{interval_id} uploaded to S3.')

    data_cache_path = os.path.join(self._data_cache, s3_key)
    os.makedirs(os.path.dirname(data_cache_path), exist_ok=True)
    if not os.path.exists(data_cache_path):  
      print(f'Loading image {tile_id}:{interval_id} into cache ({data_cache_path}).')
      self._s3.download_file(Bucket=self._s3_bucket, Key=s3_key, Filename=data_cache_path)
    else:
      print(f'Loading image {tile_id}:{interval_id} from cache ({data_cache_path}).')

    return xr.open_dataset(data_cache_path, engine='rasterio')
  
  def delete_image(self, tile_id: str, interval_id: int):
    '''
    Delete the image for a Tile ID and Interval ID.

    Parameters
    ----------
    - tile_id str: Tile ID in the format '054W_03S'
    - interval_id int: Interval ID
    '''
    s3_key = f'{self._s3_root_path}/{tile_id}/raw/{interval_id}.tif'
    
    try:
      self._s3.delete_object(Bucket=self._s3_bucket, Key=s3_key)
      data_cache_path = os.path.join(self._data_cache, s3_key)
      os.remove(data_cache_path)
    
    except Exception as e:
      pass