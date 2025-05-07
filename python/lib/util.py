import os
import rasterio
import rioxarray
import xarray as xr
import numpy as np
import dask.distributed as dd
from tqdm import tqdm
from tempfile import TemporaryDirectory
from rio_cogeo.cogeo import cog_translate
from rasterio import MemoryFile
from rio_cogeo.profiles import cog_profiles


def convert_to_cog_rio(input_geotiff, output_cog, add_mask=True):
  try:
    with MemoryFile() as memfile:
      cog_translate(input_geotiff, memfile.name, cog_profiles.get("deflate"), add_mask=add_mask)
      with open(output_cog, 'wb') as f:
        f.write(memfile.read())
  except Exception as e:
    print(f"Error converting {input_geotiff} to {output_cog}: {e}")


def fill_geotiff_stack(input_files, output_files, chunk_scheme, last_band_mask: bool = False, no_data_value = np.nan):
  '''
    Impute no data for a stack of TIFs using ffill & bfill.

    Parameters
    ----------
    - input_files: list - List of input file paths
    - output_files: list - List of output file paths
    - chunk_scheme: dict - Chunk scheme of blocks. This will be used to memory optimize the operations
    - last_band_mask: bool optional - If the last band is a mask band. It will be re-calculated with mask values of 0 & 255
    - no_data_value: optional - If the no data value to impute is other than NaN
  '''
  print('Stacking tifs in Xarray...')
  stack = xr.concat([rioxarray.open_rasterio(tif) for tif in input_files], dim='index')
  chunk_scheme['index'] = len(input_files)
  stack = stack.chunk(chunk_scheme)

  def fill_stack(block, dim_fill):
    original_dtype = block.dtype
    masked_block = block.where(block != no_data_value, np.nan)
    filled_block = masked_block.ffill(dim=dim_fill).bfill(dim=dim_fill)
    block = filled_block.where(~np.isnan(filled_block), no_data_value)
    block = block.astype(original_dtype)
  
    return block

  with TemporaryDirectory() as tdir:
    zarr_file = os.path.join(tdir, 'temp.zarr')
    
    stack = stack.map_blocks(fill_stack, kwargs={'dim_fill': 'index'}, template=stack)
    stack = stack.to_dataset(name='band_data')

    with dd.Client():
      print('\nWriting to temporary zarr file...')
      write_job = stack.to_zarr(zarr_file, mode='w', encoding={"band_data": {"fill_value": no_data_value}}, compute=False)
      write_job = write_job.persist()
      dd.progress(write_job, notebook=False)

    stack = xr.open_zarr(zarr_file, decode_coords='all', mask_and_scale=False)['band_data']

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
