import sqlite3
import numpy as np
from abc import ABC, abstractmethod
from supabase import create_client

# TODO: New attributes
# - match (stage, series_game)

# Not available in the API:
# - player (position, team_role)

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
            league_id INTEGER,
            match_id INTEGER,
            player_account_id INTEGER,
            hero_name TEXT,
            kills INTEGER,
            last_hits_at_5 INTEGER,
            heroes_on_lane TEXT,
            enemy_heroes_on_lane TEXT,
            is_radiant BOOLEAN,
            PRIMARY KEY (match_id, player_account_id)
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
            team_name TEXT,
            rating INTEGER
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_info (
            player_account_id INTEGER PRIMARY KEY,
            player_name TEXT,
            player_team_id INTEGER
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

    def insert_team_data(self, team_id, team_name, rating):
        self.cursor.execute(
            """
        INSERT OR REPLACE INTO team_info (team_id, team_name, rating)
        VALUES (?, ?, ?)
        """,
            (team_id, team_name, rating),
        )
        self.commit()
    
    def insert_player_data(self, player_account_id, player_name, player_team_id):
        self.cursor.execute(
            """
        INSERT OR REPLACE INTO player_info (player_account_id, player_name, player_team_id)
        VALUES (?, ?, ?)
        """,
            (player_account_id, player_name, player_team_id),
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
        league_id,
        match_id,
        player_account_id,
        hero_id,
        kills,
        last_hits_at_5,
        heroes_on_lane,
        enemy_heroes_on_lane,
        is_radiant,
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
        # print(f"Heroes on lane: {heroes_on_lane_str}")

        enemy_lane_heroes = []
        for hero in enemy_heroes_on_lane:
            self.cursor.execute(
                "SELECT hero_name FROM hero_info WHERE hero_id = ?", (hero,)
            )
            enemy_lane_heroes.append(self.cursor.fetchone()[0])
        enemy_heroes_on_lane_str = ", ".join(enemy_lane_heroes)
        # print(f"Enemy heroes on lane: {enemy_heroes_on_lane_str}")

        self.cursor.execute(
            """
        INSERT OR REPLACE INTO match_info (league_id, match_id, player_account_id, hero_name, kills, last_hits_at_5, heroes_on_lane, enemy_heroes_on_lane, is_radiant)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                league_id,
                match_id,
                player_account_id,
                current_hero_name,
                kills,
                last_hits_at_5,
                heroes_on_lane_str,
                enemy_heroes_on_lane_str,
                is_radiant,
            ),
        )
        self.commit()

    def get_player_avg_and_median_lh(self, player_account_id, hero_id=None):
        if hero_id is not None:
            self.cursor.execute(
                """
            SELECT last_hits_at_5 FROM match_info WHERE player_account_id = ? AND hero_id = ?
            """,
                (player_account_id, hero_id),
            )
        else:
            self.cursor.execute(
                """
            SELECT last_hits_at_5 FROM match_info WHERE player_account_id = ?
            """,
                (player_account_id,),
            )
        results = self.cursor.fetchall()

        player_stats = []
        for last_hits in results:
            player_stats.append(last_hits)

        if len(player_stats) == 0:
            return None, None
        avg_last_hits = float(np.mean(player_stats))
        median_last_hits = float(np.median(player_stats))

        return avg_last_hits, median_last_hits

    def get_player_avg_and_median_kills(self, player_account_id, hero_id=None):
        if hero_id is not None:
            self.cursor.execute(
                """
            SELECT kills FROM match_info WHERE player_account_id = ? AND hero_id = ?
            """,
                (player_account_id, hero_id),
            )
        else:
            self.cursor.execute(
                """
            SELECT kills FROM match_info WHERE player_account_id = ?
            """,
                (player_account_id,),
            )
        results = self.cursor.fetchall()

        player_stats = []
        for kills in results:
            player_stats.append(kills)

        if len(player_stats) == 0:
            return None, None
        avg_kills = float(np.mean(player_stats))
        median_kills = float(np.median(player_stats))

        return avg_kills, median_kills

    def get_hero_avg_and_median_lh(self, hero_id):
        """Get average and median last hits for a hero across all teams"""
        if hero_id is not None:
            self.cursor.execute("""
                SELECT last_hits_at_5 FROM match_info WHERE hero_id = ?
            """, (hero_id,))
        else:
            return None, None
        
        results = self.cursor.fetchall()
        if len(results) == 0:
            return None, None
        
        hero_stats = [row[0] for row in results]
        avg_last_hits = float(np.mean(hero_stats))
        median_last_hits = float(np.median(hero_stats))
        
        return avg_last_hits, median_last_hits

    def get_hero_avg_and_median_kills(self, hero_id):
        """Get average and median kills for a hero across all teams"""
        if hero_id is not None:
            self.cursor.execute("""
                SELECT kills FROM match_info WHERE hero_id = ?
            """, (hero_id,))
        else:
            return None, None
        
        results = self.cursor.fetchall()
        if len(results) == 0:
            return None, None
        
        hero_stats = [row[0] for row in results]
        avg_kills = float(np.mean(hero_stats))
        median_kills = float(np.median(hero_stats))
        
        return avg_kills, median_kills

    def get_all_leagues(self):
        """Get all leagues from the database"""
        self.cursor.execute("SELECT league_id, league_name, tier FROM league_info ORDER BY league_name")
        results = self.cursor.fetchall()
        return [{"league_id": row[0], "league_name": row[1], "tier": row[2]} for row in results]

    def get_most_recent_league(self):
        """Get the most recent league based on league_id (assuming higher ID = more recent)"""
        self.cursor.execute("SELECT league_id, league_name, tier FROM league_info ORDER BY league_id DESC LIMIT 1")
        result = self.cursor.fetchone()
        if result:
            return {"league_id": result[0], "league_name": result[1], "tier": result[2]}
        return None

    def get_team_avg_and_median_lh(self, team_id, hero_id=None):
        """Get average and median last hits for a team"""
        if hero_id is not None:
            self.cursor.execute("""
                SELECT m.last_hits_at_5 FROM match_info m
                JOIN player_info p ON m.player_account_id = p.player_account_id
                WHERE p.player_team_id = ? AND m.hero_id = ?
            """, (team_id, hero_id))
        else:
            self.cursor.execute("""
                SELECT m.last_hits_at_5 FROM match_info m
                JOIN player_info p ON m.player_account_id = p.player_account_id
                WHERE p.player_team_id = ?
            """, (team_id,))
        
        results = self.cursor.fetchall()
        if len(results) == 0:
            return None, None
        
        team_stats = [row[0] for row in results]
        avg_last_hits = float(np.mean(team_stats))
        median_last_hits = float(np.median(team_stats))
        
        return avg_last_hits, median_last_hits

    def get_team_avg_and_median_kills(self, team_id, hero_id=None):
        """Get average and median kills for a team"""
        if hero_id is not None:
            self.cursor.execute("""
                SELECT m.kills FROM match_info m
                JOIN player_info p ON m.player_account_id = p.player_account_id
                WHERE p.player_team_id = ? AND m.hero_id = ?
            """, (team_id, hero_id))
        else:
            self.cursor.execute("""
                SELECT m.kills FROM match_info m
                JOIN player_info p ON m.player_account_id = p.player_account_id
                WHERE p.player_team_id = ?
            """, (team_id,))
        
        results = self.cursor.fetchall()
        if len(results) == 0:
            return None, None
        
        team_stats = [row[0] for row in results]
        avg_kills = float(np.mean(team_stats))
        median_kills = float(np.median(team_stats))
        
        return avg_kills, median_kills

    def get_all_teams(self):
        """Get all teams from the database"""
        self.cursor.execute("SELECT team_id, team_name, rating FROM team_info ORDER BY team_name")
        results = self.cursor.fetchall()
        return [{"team_id": row[0], "team_name": row[1], "rating": row[2]} for row in results]

    def get_players_by_team(self, team_id):
        """Get players from a specific team"""
        self.cursor.execute("""
            SELECT player_account_id, player_name 
            FROM player_info 
            WHERE player_team_id = ?
            ORDER BY player_name
        """, (team_id,))
        results = self.cursor.fetchall()
        return [{"player_account_id": row[0], "player_name": row[1]} for row in results]

    def get_all_heroes(self):
        """Get all heroes from the database"""
        self.cursor.execute("SELECT hero_id, hero_name FROM hero_info ORDER BY hero_name")
        results = self.cursor.fetchall()
        return [{"hero_id": row[0], "hero_name": row[1]} for row in results]

    def get_latest_match_id(self):
        """Get the highest match_id from the match_info table"""
        self.cursor.execute("SELECT MAX(match_id) FROM match_info")
        result = self.cursor.fetchone()
        return result[0] if result and result[0] is not None else None

    def league_exists(self, league_id):
        """Check if a league already exists in the database"""
        self.cursor.execute(
            "SELECT COUNT(*) FROM league_info WHERE league_id = ?", (league_id,)
        )
        return self.cursor.fetchone()[0] > 0


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

    def insert_team_data(self, team_id, team_name, rating):
        self.client.table("team_info").upsert(
            {"team_id": team_id, "team_name": team_name, "rating": rating}
        ).execute()

    def insert_player_data(self, player_account_id, player_name, player_team_id):
        self.client.table("player_info").upsert(
            {"player_account_id": player_account_id, "player_name": player_name, "player_team_id": player_team_id}
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
        league_id,
        match_id,
        player_account_id,
        hero_id,
        kills,
        last_hits_at_5,
        heroes_on_lane,
        enemy_heroes_on_lane,
        is_radiant,
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
                "league_id": league_id,
                "match_id": match_id,
                "player_account_id": player_account_id,
                "hero_name": current_hero_name,
                "kills": kills,
                "last_hits_at_5": last_hits_at_5,
                "heroes_on_lane": heroes_on_lane_str,
                "enemy_heroes_on_lane": enemy_heroes_on_lane_str,
                "is_radiant": is_radiant,
            }
        ).execute()

    def get_player_avg_and_median_lh(self, player_account_id, hero_id=None):
        query = (
            self.client.table("match_info")
            .select("last_hits_at_5")
            .eq("player_account_id", player_account_id)
        )

        if hero_id is not None:
            query = query.eq("hero_id", hero_id)

        response = query.execute()
        results = response.data

        player_stats = []
        for result in results:
            player_stats.append(result["last_hits_at_5"])

        if len(player_stats) == 0:
            return None, None
        avg_last_hits = float(np.mean(player_stats))
        median_last_hits = float(np.median(player_stats))

        return avg_last_hits, median_last_hits

    def get_all_leagues(self):
        """Get all leagues from the database"""
        response = self.client.table("league_info").select("league_id, league_name, tier").order("league_name").execute()
        return [{"league_id": row["league_id"], "league_name": row["league_name"], "tier": row["tier"]} for row in response.data]

    def get_most_recent_league(self):
        """Get the most recent league based on league_id (assuming higher ID = more recent)"""
        response = self.client.table("league_info").select("league_id, league_name, tier").order("league_id", desc=True).limit(1).execute()
        if response.data:
            row = response.data[0]
            return {"league_id": row["league_id"], "league_name": row["league_name"], "tier": row["tier"]}
        return None

    def get_team_avg_and_median_lh(self, team_id, hero_id=None):
        """Get average and median last hits for a team"""
        # For PostgresDB, we'll need to use a different approach since joins are complex
        # For now, return placeholder values - this can be improved later
        return None, None

    def get_team_avg_and_median_kills(self, team_id, hero_id=None):
        """Get average and median kills for a team"""
        # For PostgresDB, we'll need to use a different approach since joins are complex
        # For now, return placeholder values - this can be improved later
        return None, None

    def get_hero_avg_and_median_lh(self, hero_id):
        """Get average and median last hits for a hero across all teams"""
        # For PostgresDB, we'll need to use a different approach since joins are complex
        # For now, return placeholder values - this can be improved later
        return None, None

    def get_hero_avg_and_median_kills(self, hero_id):
        """Get average and median kills for a hero across all teams"""
        # For PostgresDB, we'll need to use a different approach since joins are complex
        # For now, return placeholder values - this can be improved later
        return None, None

    def get_players_by_team(self, team_id):
        """Get players from a specific team"""
        response = self.client.table("player_info").select("player_account_id, player_name").eq("player_team_id", team_id).order("player_name").execute()
        return [{"player_account_id": row["player_account_id"], "player_name": row["player_name"]} for row in response.data]

    def get_all_heroes(self):
        """Get all heroes from the database"""
        response = self.client.table("hero_info").select("hero_id, hero_name").order("hero_name").execute()
        return [{"hero_id": row["hero_id"], "hero_name": row["hero_name"]} for row in response.data]

    def get_latest_match_id(self):
        """Get the highest match_id from the match_info table"""
        response = (
            self.client.table("match_info")
            .select("match_id")
            .order("match_id", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0]["match_id"] if response.data else None

    def league_exists(self, league_id):
        """Check if a league already exists in the database"""
        response = (
            self.client.table("league_info")
            .select("league_id")
            .eq("league_id", league_id)
            .execute()
        )
        return len(response.data) > 0
