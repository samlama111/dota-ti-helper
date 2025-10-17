from peewee import SqliteDatabase

file_path_prefix = "new_data/"
sqlite_db_path = file_path_prefix + "dota_2_data_2025_10_15-2025-10-17.db"

db = SqliteDatabase(sqlite_db_path)
