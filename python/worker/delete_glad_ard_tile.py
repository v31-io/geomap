from dotenv import load_dotenv
load_dotenv(override=True)

from argparse import ArgumentParser

from ..lib.glad import GLAD


parser = ArgumentParser(description='Delete all images for GLAD ARD Tile ID')
parser.add_argument('tile_id', help='Tile ID')
args = parser.parse_args()
tile_id = args.tile_id

glad = GLAD()

glad.delete_tile(tile_id=tile_id)