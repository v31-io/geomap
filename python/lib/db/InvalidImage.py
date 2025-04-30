from peewee import Model, CompositeKey, TextField, FixedCharField, IntegerField, FloatField

from .db import db


class InvalidImage(Model):
  tile_id = FixedCharField(8)
  interval_id = IntegerField()
  reason = TextField()
  valid_pixel_percentage = FloatField()

  class Meta:
    database = db
    primary_key = CompositeKey('tile_id', 'interval_id')

  def get_lat(self):
    return self.tile_id[5:8]
  
  def get_lon(self):
    return self.tile_id[0:4]
  
db.create_tables([InvalidImage])