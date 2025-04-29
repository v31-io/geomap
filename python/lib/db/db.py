import os
from peewee import PostgresqlDatabase

db = PostgresqlDatabase(os.environ['POSTGRES_DB'], user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD'],
                           host=os.environ['POSTGRES_URL'], port=5432)

db.connect()