from playhouse.sqlite_ext import SqliteExtDatabase


file_path_prefix = "db_cache/"
sqlite_db_path = file_path_prefix + "api_cache.db"

db = SqliteExtDatabase(
    sqlite_db_path,
    pragmas=(
        ("cache_size", -1024 * 64),  # 64MB page-cache.
        ("journal_mode", "wal"),  # Use WAL-mode (you should always use this!).
        ("foreign_keys", 1),  # Enforce foreign-key constraints.
    ),
)
