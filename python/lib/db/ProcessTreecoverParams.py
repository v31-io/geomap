from peewee import Model, FixedCharField, FloatField

from .db import db


class ProcessTreecoverParams(Model):
  tile_id = FixedCharField(8, primary_key=True)
  ndvi_diff_cut_trees = FloatField()
  ndvi_tree_lower_bound = FloatField()

  class Meta:
    database = db
  
db.create_tables([ProcessTreecoverParams])