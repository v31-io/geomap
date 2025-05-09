from dotenv import load_dotenv
load_dotenv()

from argparse import ArgumentParser

from ..lib.glad import GLAD


parser = ArgumentParser(description='Process RGBA for GLAD ARD Tile ID')
parser.add_argument('tile_id', help='Tile ID')
args = parser.parse_args()
tile_id = args.tile_id

glad = GLAD()

glad.process_images_rgba(tile_id=tile_id)