import sqlite3
import numpy as np


def create_db():
    conn = sqlite3.connect("matches.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS match_info (
        match_id INTEGER,
        player_name TEXT,
        hero_id INTEGER,
        kills INTEGER,
        last_hits_at_5 INTEGER,
        PRIMARY KEY (match_id, player_name)
    )
    """)
    conn.commit()
    conn.close()


def insert_match_data(match_id, player_name, hero_id, kills, last_hits_at_5):
    conn = sqlite3.connect("matches.db")
    cursor = conn.cursor()
    cursor.execute(
        """
    INSERT OR REPLACE INTO match_info (match_id, player_name, hero_id, kills, last_hits_at_5)
    VALUES (?, ?, ?, ?, ?)
    """,
        (match_id, player_name, hero_id, kills, last_hits_at_5),
    )
    conn.commit()
    conn.close()


def get_avg_and_median_lh_based_player_prefix(prefix, hero_id=None):
    conn = sqlite3.connect("matches.db")
    cursor = conn.cursor()
    if hero_id is not None:
        cursor.execute(
            """
        SELECT player_name, last_hits_at_5 FROM match_info WHERE player_name LIKE ? AND hero_id = ?
        """,
            (prefix + "%", hero_id),
        )
    else:
        cursor.execute(
            """
        SELECT player_name, last_hits_at_5 FROM match_info WHERE player_name LIKE ?
        """,
            (prefix + "%",),
        )
    results = cursor.fetchall()
    conn.close()

    player_stats = {}
    for player_name, last_hits in results:
        if player_name not in player_stats:
            player_stats[player_name] = []
        player_stats[player_name].append(last_hits)

    avg_and_median = []
    for player_name, last_hits in player_stats.items():
        avg_last_hits = float(np.mean(last_hits))
        median_last_hits = float(np.median(last_hits))
        avg_and_median.append((player_name, avg_last_hits, median_last_hits))

    return avg_and_median


def get_avg_and_median_kills_based_player_prefix(prefix, hero_id=None):
    conn = sqlite3.connect("matches.db")
    cursor = conn.cursor()
    if hero_id is not None:
        cursor.execute(
            """
        SELECT player_name, kills FROM match_info WHERE player_name LIKE ? AND hero_id = ?
        """,
            (prefix + "%", hero_id),
        )
    else:
        cursor.execute(
            """
        SELECT player_name, kills FROM match_info WHERE player_name LIKE ?
        """,
            (prefix + "%",),
        )
    results = cursor.fetchall()
    conn.close()

    player_stats = {}
    for player_name, kills in results:
        if player_name not in player_stats:
            player_stats[player_name] = []
        player_stats[player_name].append(kills)

    avg_and_median = []
    for player_name, kills in player_stats.items():
        avg_kills = float(np.mean(kills))
        median_kills = float(np.median(kills))
        avg_and_median.append((player_name, avg_kills, median_kills))

    return avg_and_median


def get_all_players():
    conn = sqlite3.connect("matches.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT player_name FROM match_info")
    results = cursor.fetchall()
    conn.close()
    return [row[0] for row in results]
