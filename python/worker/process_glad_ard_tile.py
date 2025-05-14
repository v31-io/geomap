from dotenv import load_dotenv
load_dotenv()

from argparse import ArgumentParser

from ..lib.glad import GLAD


parser = ArgumentParser(description='Process RGBA for GLAD ARD Tile ID')
parser.add_argument('tile_id', help='Tile ID')
parser.add_argument('level', help='Level', choices=['rgba', 'treecover'])
args = parser.parse_args()
tile_id = args.tile_id
level = args.level

glad = GLAD()

if level == 'rgba':
  glad.process_images_rgba(tile_id=tile_id)
elif level == 'treecover':
  glad.process_images_treecover(tile_id=tile_id)
else:
  raise Exception(f'Invalid level {level}.')