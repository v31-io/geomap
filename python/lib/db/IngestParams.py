from peewee import Model, FixedCharField, FloatField

from .db import db


class IngestParams(Model):
  tile_id = FixedCharField(8, primary_key=True)
  valid_image_pixels = FloatField()

  class Meta:
    database = db
  
db.create_tables([IngestParams])