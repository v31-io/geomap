from lib.glad import GLAD

glad = GLAD()

def update_tiles():
  print('Updating tiles cache...')
  return {
    'base_url': glad.get_image_base_url(),
    'tiles': glad.list_tiles(full=True)
  }
print('Updated tiles cache...')