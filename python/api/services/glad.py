from datetime import datetime

from lib.glad import GLAD


glad = GLAD()

attributions = '''Landsat Analysis Ready Data (GLAD ARD) used from https://glad.umd.edu/ard/home.
Potapov, P., Hansen, M.C., Kommareddy, I., Kommareddy, A., Turubanova, S., Pickens, A., Adusei, B., Tyukavina A., and Ying, Q., 2020.
Landsat analysis ready data for global land cover and land cover change mapping. 
Remote Sens. 2020, 12, 426; doi:10.3390/rs12030426
'''
base_url = glad.get_image_base_url()


def update_layers():
  print('Updating layers cache...')

  tiles = glad.list_tiles(full=True)

  layers = [{
    'zlevel': 2,
    'name': 'Tree Cover',
    'layer': 'treecover',
    'visible': True,
    'bands': 1,
    'style': {
      'color': [
        # Nodata/NaN is transparent
        'case',
        ['==', ['band', 2], 0],
        [0, 0, 0, 0],
        # Tree cover is green and non-treecover is red
        ["interpolate", ["linear"], ["band", 1],
          0, [20, 90, 50], 1, [250, 0, 0]]
      ]
    },
    'min': 0,
    'max': 1
  }, {
    'zlevel': 1,
    'name': 'True Color Image',
    'layer': 'rgba',
    'visible': False,
    'bands': 4,
    'style': {
      # RGBA
      'color': ["array", ['band', 1], ['band', 2], ['band', 3], ['band', 4]],
      'gamma': 1.1
    },
    'min': 0,
    'max': 255
  }]

  for layer in layers:
    layer['tiles'] = []
    for tile, images in tiles.items():
      for image in images:
        layer['tiles'].append({
          'url': f'{base_url}/{tile}/{image["ID"]}/{layer["layer"]}.tif',
          'tile': tile,
          'id': image['ID'],
          'date': image['Date']
        })

  print('Updated layers cache...')
  return layers


def filter_dates(layers: dict, date: datetime):
  '''
    Return layers filtered to a date. Return the closest previous image to the date.

    Parameters
    ----------
    - layers: dict - All layers metadata.
    - date: datetime - Date to filter to. Defaults to today.
  '''
  if date is None:
    date = datetime.now()

  def _filter_dates(row):
    return date > row['date']

  # Get only latest image of each Tile
  for layer in layers:
    tiles = []
    tiles_set = set()
    layer['tiles'] = list(filter(_filter_dates, layer['tiles']))
    for tile in reversed(layer['tiles']):
      if tile['tile'] not in tiles_set:
        tiles.append(tile)
        tiles_set.add(tile['tile'])
    layer['tiles'] = tiles

  return layers


def get_meta():
  return {
    'attributions': attributions,
    'geojson': glad.get_tile_geojson().to_geo_dict()
  }