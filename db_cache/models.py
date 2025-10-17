from datetime import datetime

from peewee import CharField, DateTimeField, Model
from playhouse.sqlite_ext import JSONField

from db_cache.db_connection import db


class BaseModel(Model):
    class Meta:
        database = db


class ApiCache(BaseModel):
    endpoint = CharField(primary_key=True)
    response_data = JSONField()
    timestamp = DateTimeField(default=datetime.now)
