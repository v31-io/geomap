import os
import warnings
import rasterio
import shutil
import xarray as xr
import numpy as np
import dask.distributed as dd
from tqdm import tqdm
from tempfile import TemporaryDirectory
from rio_cogeo.cogeo import cog_translate
from rasterio import MemoryFile
from rio_cogeo.profiles import cog_profiles


warnings.filterwarnings(action='ignore', category=UserWarning, 
                        message="Consolidated metadata is currently not part in the Zarr format 3 specification. It "
                                "may not be supported by other zarr implementations and may change in the future.")


def convert_to_cog_rio(input_geotiff: str, output_cog: str, add_mask: bool = True):
  '''
    Convert a GeoTIFF to a Cloud Optimized GeoTIFF

    Parameters
    ----------
    - input_geotiff: str - Input GeoTIFF path
    - output_cog: str - Output GeoTIFF path
    - add_mask: bool optional - Force output dataset creation with a mask.
  '''
  try:
    with MemoryFile() as memfile:
      cog_translate(input_geotiff, memfile.name, cog_profiles.get("deflate"), add_mask=add_mask)
      with open(output_cog, 'wb') as f:
        f.write(memfile.read())
  except Exception as e:
    print(f"Error converting {input_geotiff} to {output_cog}: {e}")

def fill_geotiff_stack(input_files: list, output_files: list, block_size: int, last_band_mask: bool = False, no_data_value = np.nan):
  '''
    Impute no data for a stack of TIFs using ffill & bfill.

    Parameters
    ----------
    - input_files: list - List of input file paths
    - output_files: list - List of output file paths
    - block_size: int - Block size of x & y dimension. Used to optimize for memory
    - last_band_mask: bool optional - If the last band is a mask band. It will be re-calculated with mask values of 0 & 255
    - no_data_value: optional - If the no data value to impute is other than NaN
  '''
  with TemporaryDirectory() as tdir:
    print('Stacking tifs in Xarray...')
    stack_paths = []
    for i, file in tqdm(enumerate(input_files), total=len(input_files)):
      ds = xr.open_dataset(file, engine='rasterio', decode_coords='all', mask_and_scale=False).drop_vars('spatial_ref')
      ds = ds.chunk({'band': 1, 'x': block_size, 'y': block_size})
      zarr_file_temp = os.path.join(tdir, f'{i}.zarr')
      ds.to_zarr(zarr_file_temp, mode='w', encoding={"band_data": {"fill_value": no_data_value}})
      stack_paths.append(zarr_file_temp)

    print('\nWriting to stacked zarr...')
    stack = xr.concat([xr.open_dataset(file, mask_and_scale=False) for file in stack_paths], dim='index')
    stack = stack.chunk({'index': len(input_files), 'band': 1, 'x': block_size, 'y': block_size})
    zarr_file_stacked = os.path.join(tdir, 'temp.zarr')
    stack.to_zarr(zarr_file_stacked, mode='w', encoding={"band_data": {"fill_value": no_data_value}})
    stack = xr.open_zarr(zarr_file_stacked, mask_and_scale=False)

    for file in stack_paths:
      shutil.rmtree(file)

    def fill_stack(block, dim_fill):
      original_dtype = block.dtype
      masked_block = block.where(block != no_data_value, np.nan)
      filled_block = masked_block.ffill(dim=dim_fill).bfill(dim=dim_fill)
      block = filled_block.where(~np.isnan(filled_block), no_data_value)
      block = block.astype(original_dtype)
    
      return block

    stack['band_data'] = stack['band_data'].map_blocks(fill_stack, kwargs={'dim_fill': 'index'}, 
                                                       template=stack['band_data'])

    zarr_file_filled = os.path.join(tdir, 'temp2.zarr')
    with dd.Client():
      print('\nPerforming fill on stacked zarr...')
      write_job = stack.to_zarr(zarr_file_filled, mode='w', compute=False)
      write_job = write_job.persist()
      dd.progress(write_job, notebook=False)

    stack = xr.open_zarr(zarr_file_filled, mask_and_scale=False)['band_data']
    shutil.rmtree(zarr_file_stacked)

    print('\nWriting to tifs...')
    for index in tqdm(stack['index'].values):
      with rasterio.open(input_files[index], mode='r') as src:
        bands = stack.isel(index=index).values
        if last_band_mask:
          num_bands = bands.shape[0] - 1
          mask = np.all(bands[0:num_bands] == no_data_value, axis=0)
          bands[num_bands] = np.where(mask, 0, 255)

        new_meta = src.meta.copy()

        with rasterio.open(output_files[index], 'w', **new_meta) as dst:
          dst.write(bands)
