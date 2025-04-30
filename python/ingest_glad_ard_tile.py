from dotenv import load_dotenv
load_dotenv()

from tqdm import tqdm
from argparse import ArgumentParser

from .lib.glad import GLAD


parser = ArgumentParser(description='Ingest valid GLAD ARD Tile Images')
parser.add_argument('tile_id', help='Tile ID')
args = parser.parse_args()
tile_id = args.tile_id

glad = GLAD()

valid_ids = glad.get_valid_ids(tile_id=tile_id)
print(f'{len(valid_ids)} IDs found for ingestion.')

for id in tqdm(valid_ids):
  glad.get_image(tile_id=tile_id, interval_id=id)