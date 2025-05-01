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