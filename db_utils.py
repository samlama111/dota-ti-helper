import sqlite3
import numpy as np

# TODO: New attributes

class DB:
    def __init__(self, file_path):
        self.file_path = file_path
        self.conn = sqlite3.connect(file_path)
        self.cursor = self.conn.cursor()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def create_db(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_info (
            tournament_id INTEGER,
            match_id INTEGER,
            player_name TEXT,
            hero_name TEXT,
            kills INTEGER,
            last_hits_at_5 INTEGER,
            heroes_on_lane TEXT,
            enemy_heroes_on_lane TEXT,
            team_id INTEGER,
            PRIMARY KEY (match_id, player_name)
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS hero_info (
            hero_id INTEGER PRIMARY KEY,
            hero_name TEXT
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS league_info (
            league_id INTEGER PRIMARY KEY,
            league_name TEXT,
            tier TEXT,
            patch_id INTEGER
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_info (
            team_id INTEGER PRIMARY KEY,
            team_name TEXT
        )
        """)
        self.conn.commit()

    def insert_hero_data(self, hero_id, hero_name):
        self.cursor.execute(
            """
        INSERT OR REPLACE INTO hero_info (hero_id, hero_name)
        VALUES (?, ?)
        """,
            (hero_id, hero_name),
        )
        self.conn.commit()
    
    def insert_team_data(self, team_id, team_name):
        self.cursor.execute(
            """
        INSERT OR REPLACE INTO team_info (team_id, team_name)
        VALUES (?, ?)
        """,
            (team_id, team_name),
        )
        self.conn.commit()
    
    def insert_league_data(self, league_id, league_name, tier, patch_id):
        self.cursor.execute(
            """
        INSERT OR REPLACE INTO league_info (league_id, league_name, tier, patch_id)
        VALUES (?, ?, ?, ?)
        """,
            (league_id, league_name, tier, patch_id),
        )
        self.conn.commit()

    def insert_match_data(
        self,
        tournament_id,
        match_id,
        player_name,
        hero_id,
        kills,
        last_hits_at_5,
        heroes_on_lane,
        enemy_heroes_on_lane,
        team_id
    ):
        # Get hero_name from hero_info table
        self.cursor.execute("SELECT hero_name FROM hero_info WHERE hero_id = ?", (hero_id,))
        current_hero_name = self.cursor.fetchone()[0]
        if current_hero_name is None:
            raise ValueError(f"Hero with id {hero_id} not found")

        lane_heroes = []
        for hero in heroes_on_lane:
            self.cursor.execute("SELECT hero_name FROM hero_info WHERE hero_id = ?", (hero,))
            lane_heroes.append(self.cursor.fetchone()[0])
        heroes_on_lane_str = ", ".join(lane_heroes)
        print(f"Heroes on lane: {heroes_on_lane_str}")

        enemy_lane_heroes = []
        for hero in enemy_heroes_on_lane:
            self.cursor.execute("SELECT hero_name FROM hero_info WHERE hero_id = ?", (hero,))
            enemy_lane_heroes.append(self.cursor.fetchone()[0])
        enemy_heroes_on_lane_str = ", ".join(enemy_lane_heroes)
        print(f"Enemy heroes on lane: {enemy_heroes_on_lane_str}")

        self.cursor.execute(
            """
        INSERT OR REPLACE INTO match_info (tournament_id, match_id, player_name, hero_name, kills, last_hits_at_5, heroes_on_lane, enemy_heroes_on_lane, team_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                tournament_id,
                match_id,
                player_name,
                current_hero_name,
                kills,
                last_hits_at_5,
                heroes_on_lane_str,
                enemy_heroes_on_lane_str,
                team_id
            ),
        )
        self.conn.commit()

    def get_avg_and_median_lh_based_player_prefix(self, prefix, hero_id=None):
        if hero_id is not None:
            self.cursor.execute(
                """
            SELECT player_name, last_hits_at_5 FROM match_info WHERE player_name LIKE ? AND hero_id = ?
            """,
                (prefix + "%", hero_id),
            )
        else:
            self.cursor.execute(
                """
            SELECT player_name, last_hits_at_5 FROM match_info WHERE player_name LIKE ?
            """,
                (prefix + "%",),
            )
        results = self.cursor.fetchall()

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

    def get_avg_and_median_kills_based_player_prefix(self, prefix, hero_id=None):
        if hero_id is not None:
            self.cursor.execute(
                """
            SELECT player_name, kills FROM match_info WHERE player_name LIKE ? AND hero_id = ?
            """,
            (prefix + "%", hero_id),
        )
        else:
            self.cursor.execute(
                """
            SELECT player_name, kills FROM match_info WHERE player_name LIKE ?
            """,
                (prefix + "%",),
            )
        results = self.cursor.fetchall()

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

    def get_all_players(self):
        self.cursor.execute("SELECT DISTINCT player_name FROM match_info")
        results = self.cursor.fetchall()
        return [row[0] for row in results]
