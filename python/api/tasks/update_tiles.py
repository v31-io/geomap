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
    'tiles': glad.list_tiles(full=True)
  }
print('Updated tiles cache...')