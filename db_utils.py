import sqlite3
import numpy as np
from abc import ABC, abstractmethod
from supabase import create_client

# TODO: New attributes
# - player (position, team_role)
# - team (current player_ids, their elo rating)
# - tournament (stage, series_game)
# - hero (role, pick_order)
# - match (side, who won)

# New view (inference-time, not stored in db)
# - player_hero_games, player_hero_avg_lh_5, player_hero_std_lh_5, player_hero_avg_kills


class BaseDB(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def commit(self):
        pass


class SQLiteDB(BaseDB):
    def __init__(self, file_path):
        self.file_path = file_path
        self.connect()

    def connect(self):
        self.conn = sqlite3.connect(self.file_path)
        self.cursor = self.conn.cursor()

    def close(self):
        if self.conn:
            self.conn.close()

    def commit(self):
        self.conn.commit()

    def create_db(self):
        """Create database tables - common for both implementations"""
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
        self.commit()

    def insert_hero_data(self, hero_id, hero_name):
        self.cursor.execute(
            """
        INSERT OR REPLACE INTO hero_info (hero_id, hero_name)
        VALUES (?, ?)
        """,
            (hero_id, hero_name),
        )
        self.commit()

    def insert_team_data(self, team_id, team_name):
        self.cursor.execute(
            """
        INSERT OR REPLACE INTO team_info (team_id, team_name)
        VALUES (?, ?)
        """,
            (team_id, team_name),
        )
        self.commit()

    def insert_league_data(self, league_id, league_name, tier, patch_id):
        self.cursor.execute(
            """
        INSERT OR REPLACE INTO league_info (league_id, league_name, tier, patch_id)
        VALUES (?, ?, ?, ?)
        """,
            (league_id, league_name, tier, patch_id),
        )
        self.commit()

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
        team_id,
    ):
        # Get hero_name from hero_info table
        self.cursor.execute(
            "SELECT hero_name FROM hero_info WHERE hero_id = ?", (hero_id,)
        )
        current_hero_name = self.cursor.fetchone()[0]
        if current_hero_name is None:
            raise ValueError(f"Hero with id {hero_id} not found")

        lane_heroes = []
        for hero in heroes_on_lane:
            self.cursor.execute(
                "SELECT hero_name FROM hero_info WHERE hero_id = ?", (hero,)
            )
            lane_heroes.append(self.cursor.fetchone()[0])
        heroes_on_lane_str = ", ".join(lane_heroes)
        print(f"Heroes on lane: {heroes_on_lane_str}")

        enemy_lane_heroes = []
        for hero in enemy_heroes_on_lane:
            self.cursor.execute(
                "SELECT hero_name FROM hero_info WHERE hero_id = ?", (hero,)
            )
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
                team_id,
            ),
        )
        self.commit()

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


class PostgresDB(BaseDB):
    def __init__(self, supabase_url, supabase_key):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.connect()

    def connect(self):
        self.client = create_client(self.supabase_url, self.supabase_key)

    def close(self):
        # Supabase client doesn't require explicit closing
        pass

    def commit(self):
        # Supabase automatically commits transactions
        pass

    def insert_hero_data(self, hero_id, hero_name):
        self.client.table("hero_info").upsert(
            {"hero_id": hero_id, "hero_name": hero_name}
        ).execute()

    def insert_team_data(self, team_id, team_name):
        self.client.table("team_info").upsert(
            {"team_id": team_id, "team_name": team_name}
        ).execute()

    def insert_league_data(self, league_id, league_name, tier, patch_id):
        self.client.table("league_info").upsert(
            {
                "league_id": league_id,
                "league_name": league_name,
                "tier": tier,
                "patch_id": patch_id,
            }
        ).execute()

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
        team_id,
    ):
        # Get hero_name from hero_info table
        response = (
            self.client.table("hero_info")
            .select("hero_name")
            .eq("hero_id", hero_id)
            .execute()
        )
        if not response.data:
            raise ValueError(f"Hero with id {hero_id} not found")
        current_hero_name = response.data[0]["hero_name"]

        # Get hero names for heroes on lane
        lane_heroes = []
        for hero in heroes_on_lane:
            response = (
                self.client.table("hero_info")
                .select("hero_name")
                .eq("hero_id", hero)
                .execute()
            )
            if response.data:
                lane_heroes.append(response.data[0]["hero_name"])
        heroes_on_lane_str = ", ".join(lane_heroes)

        # Get hero names for enemy heroes on lane
        enemy_lane_heroes = []
        for hero in enemy_heroes_on_lane:
            response = (
                self.client.table("hero_info")
                .select("hero_name")
                .eq("hero_id", hero)
                .execute()
            )
            if response.data:
                enemy_lane_heroes.append(response.data[0]["hero_name"])
        enemy_heroes_on_lane_str = ", ".join(enemy_lane_heroes)

        # Insert match data
        self.client.table("match_info").upsert(
            {
                "tournament_id": tournament_id,
                "match_id": match_id,
                "player_name": player_name,
                "hero_name": current_hero_name,
                "kills": kills,
                "last_hits_at_5": last_hits_at_5,
                "heroes_on_lane": heroes_on_lane_str,
                "enemy_heroes_on_lane": enemy_heroes_on_lane_str,
                "team_id": team_id,
            }
        ).execute()

    def get_avg_and_median_lh_based_player_prefix(self, prefix, hero_id=None):
        query = (
            self.client.table("match_info")
            .select("player_name, last_hits_at_5")
            .like("player_name", f"{prefix}%")
        )

        if hero_id is not None:
            query = query.eq("hero_id", hero_id)

        response = query.execute()
        results = response.data

        player_stats = {}
        for result in results:
            player_name = result["player_name"]
            last_hits = result["last_hits_at_5"]
            if player_name not in player_stats:
                player_stats[player_name] = []
            player_stats[player_name].append(last_hits)

        avg_and_median = []
        for player_name, last_hits in player_stats.items():
            avg_last_hits = float(np.mean(last_hits))
            median_last_hits = float(np.median(last_hits))
            avg_and_median.append((player_name, avg_last_hits, median_last_hits))

        return avg_and_median

    def get_all_players(self):
        response = self.client.table("match_info").select("player_name").execute()
        unique_players = set(result["player_name"] for result in response.data)
        return list(unique_players)
