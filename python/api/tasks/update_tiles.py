from lib.glad import GLAD

glad = GLAD()

attributions = '''
Landsat Analysis Ready Data (GLAD ARD) used from https://glad.umd.edu/ard/home.
Potapov, P., Hansen, M.C., Kommareddy, I., Kommareddy, A., Turubanova, S., Pickens, A., Adusei, B., Tyukavina A., and Ying, Q., 2020.
Landsat analysis ready data for global land cover and land cover change mapping. 
Remote Sens. 2020, 12, 426; doi:10.3390/rs12030426
'''

def update_tiles():
  print('Updating tiles cache...')
  return {
    'base_url': glad.get_image_base_url(),
    # Layer on Open Layer UI Map appear in reversed order
    'layers': [
      {
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
      },
      {
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
            ["interpolate", ["linear"], ["band", 1], 0, [20, 90, 50], 1, [250, 0, 0]]
          ]
        },
        'min': 0,
        'max': 1
      }
    ],
    'tiles': glad.list_tiles(full=True),
    'alltiles': glad.get_tile_geojson().to_geo_dict(),
    'attributions': attributions
  }
print('Updated tiles cache...')