from lib.glad import GLAD

glad = GLAD()

def update_tiles():
  print('Updating tiles cache...')
  return {
    'base_url': glad.get_image_base_url(),
    # Layer on Open Layer UI Map appear in reversed order
    'layers': [
      {
      'name': 'True Color Image',
      'layer': 'rgba'
      }
    ],
    'tiles': glad.list_tiles(full=True),
    'attributions': 'Landsat Analysis Ready Data (GLAD ARD) used from https://glad.umd.edu/ard/home. \nPotapov, P., Hansen, M.C., Kommareddy, I., Kommareddy, A., Turubanova, S., Pickens, A., Adusei, B., Tyukavina A., and Ying, Q., 2020. \nLandsat analysis ready data for global land cover and land cover change mapping. \nRemote Sens. 2020, 12, 426; doi:10.3390/rs12030426'
  }
print('Updated tiles cache...')