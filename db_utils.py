import sqlite3
import numpy as np


def create_db():
    conn = sqlite3.connect("matches.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS match_info (
        tournament_id INTEGER,
        match_id INTEGER,
        player_name TEXT,
        hero_name TEXT,
        kills INTEGER,
        last_hits_at_5 INTEGER,
        heroes_on_lane TEXT,
        PRIMARY KEY (match_id, player_name)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hero_info (
        hero_id INTEGER PRIMARY KEY,
        hero_name TEXT
    )
    """)
    conn.commit()
    conn.close()


def insert_hero_data(hero_id, hero_name):
    conn = sqlite3.connect("matches.db")
    cursor = conn.cursor()
    cursor.execute(
        """
    INSERT OR REPLACE INTO hero_info (hero_id, hero_name)
    VALUES (?, ?)
    """,
        (hero_id, hero_name),
    )
    conn.commit()
    conn.close()


def insert_match_data(
    tournament_id, match_id, player_name, hero_id, kills, last_hits_at_5,
    heroes_on_lane,
):
    conn = sqlite3.connect("matches.db")
    cursor = conn.cursor()
    # Get hero_name from hero_info table
    cursor.execute("SELECT hero_name FROM hero_info WHERE hero_id = ?", (hero_id,))
    current_hero_name = cursor.fetchone()[0]
    if current_hero_name is None:
        raise ValueError(f"Hero with id {hero_id} not found")

    # Get hero_name from hero_info table
    lane_heroes = []
    for hero in heroes_on_lane:
        cursor.execute("SELECT hero_name FROM hero_info WHERE hero_id = ?", (hero,))
        lane_heroes.append(cursor.fetchone()[0])
    heroes_on_lane_str = ", ".join(lane_heroes)
    print(f"Heroes on lane: {heroes_on_lane_str}")

    cursor.execute(
        """
    INSERT OR REPLACE INTO match_info (tournament_id, match_id, player_name, hero_name, kills, last_hits_at_5, heroes_on_lane)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            tournament_id,
            match_id,
            player_name,
            current_hero_name,
            kills,
            last_hits_at_5,
            heroes_on_lane_str,
        ),
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
