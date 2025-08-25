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
            hero_id INTEGER,
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
        INSERT OR REPLACE INTO match_info (league_id, match_id, player_account_id, hero_id, kills, last_hits_at_5, heroes_on_lane, enemy_heroes_on_lane, is_radiant)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                league_id,
                match_id,
                player_account_id,
                hero_id,
                kills,
                last_hits_at_5,
                heroes_on_lane_str,
                enemy_heroes_on_lane_str,
                is_radiant,
            ),
        )
        self.commit()

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

    def get_lane_matchups(self, hero_id, friendly_hero_name=None, enemy_hero_names=None, is_radiant=None):
        """Get lane matchup statistics for a hero against specific friendly and enemy heroes"""
        query = """
            SELECT 
                m.last_hits_at_5,
                m.kills,
                m.heroes_on_lane,
                m.enemy_heroes_on_lane,
                m.is_radiant,
                m.match_id
            FROM match_info m
            WHERE m.hero_id = ?
        """
        params = [hero_id]
        
        if friendly_hero_name:
            query += " AND m.heroes_on_lane LIKE ?"
            params.append(f"%{friendly_hero_name}%")
        
        if enemy_hero_names:
            if len(enemy_hero_names) == 1:
                query += " AND m.enemy_heroes_on_lane LIKE ?"
                params.append(f"%{enemy_hero_names[0]}%")
            else:
                # For multiple enemy heroes, check if both are present
                placeholders = " AND ".join([f"m.enemy_heroes_on_lane LIKE ?" for _ in enemy_hero_names])
                query += f" AND ({placeholders})"
                params.extend([f"%{ename}%" for ename in enemy_hero_names])
        
        if is_radiant is not None:
            query += " AND m.is_radiant = ?"
            params.append(is_radiant)
        
        self.cursor.execute(query, params)
        results = self.cursor.fetchall()
        
        if not results:
            return None, None, None, None
        
        last_hits = [row[0] for row in results]
        kills = [row[1] for row in results]
        
        avg_last_hits = float(np.mean(last_hits))
        median_last_hits = float(np.median(last_hits))
        avg_kills = float(np.mean(kills))
        median_kills = float(np.median(kills))
        
        return avg_last_hits, median_last_hits, avg_kills, median_kills

    def get_hero_performance_by_side(self, hero_id, is_radiant):
        """Get hero performance statistics for a specific side (Radiant/Dire)"""
        self.cursor.execute("""
            SELECT last_hits_at_5, kills
            FROM match_info 
            WHERE hero_id = ? AND is_radiant = ?
        """, (hero_id, is_radiant))
        
        results = self.cursor.fetchall()
        if not results:
            return None, None, None, None
        
        last_hits = [row[0] for row in results]
        kills = [row[1] for row in results]
        
        avg_last_hits = float(np.mean(last_hits))
        median_last_hits = float(np.median(last_hits))
        avg_kills = float(np.mean(kills))
        median_kills = float(np.median(kills))
        
        return avg_last_hits, median_last_hits, avg_kills, median_kills

    def get_matchup_statistics(self, hero_id, enemy_hero_name, is_radiant=None):
        """Get specific hero vs hero matchup statistics"""
        query = """
            SELECT last_hits_at_5, kills
            FROM match_info 
            WHERE hero_id = ? AND enemy_heroes_on_lane LIKE ?
        """
        params = [hero_id, f"%{enemy_hero_name}%"]
        
        if is_radiant is not None:
            query += " AND m.is_radiant = ?"
            params.append(is_radiant)
        
        self.cursor.execute(query, params)
        results = self.cursor.fetchall()
        
        if not results:
            return None, None, None, None
        
        last_hits = [row[0] for row in results]
        kills = [row[1] for row in results]
        
        avg_last_hits = float(np.mean(last_hits))
        median_last_hits = float(np.median(last_hits))
        avg_kills = float(np.mean(kills))
        median_kills = float(np.median(kills))
        
        return avg_last_hits, median_last_hits, avg_kills, median_kills

    def get_hero_name_by_id(self, hero_id):
        """Get hero name by hero ID"""
        self.cursor.execute("SELECT hero_name FROM hero_info WHERE hero_id = ?", (hero_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_heroes_played_by_player(self, player_account_id):
        """Get all heroes that a specific player has played"""
        self.cursor.execute("""
            SELECT DISTINCT h.hero_id, h.hero_name
            FROM hero_info h
            JOIN match_info m ON h.hero_id = m.hero_id
            WHERE m.player_account_id = ?
            ORDER BY h.hero_name
        """, (player_account_id,))
        
        results = self.cursor.fetchall()
        return [{"hero_id": row[0], "hero_name": row[1]} for row in results]

    def get_comprehensive_stats(self, metric, filters=None):
        """
        Get comprehensive statistics for a given metric with optional filters
        
        Args:
            metric: 'last_hits_at_5' or 'kills'
            filters: dict with optional keys: player_id, hero_id, team_id, league_id, patch_id
        
        Returns:
            dict with: count, mean, median, std, min, max, q25, q75
        """
        # Build the WHERE clause based on filters
        where_conditions = []
        params = []
        
        if filters:
            if filters.get('player_id'):
                where_conditions.append("m.player_account_id = ?")
                params.append(filters['player_id'])
            if filters.get('hero_id'):
                where_conditions.append("m.hero_id = ?")
                params.append(filters['hero_id'])
            if filters.get('team_id'):
                where_conditions.append("m.player_account_id IN (SELECT player_account_id FROM player_info WHERE player_team_id = ?)")
                params.append(filters['team_id'])
            if filters.get('league_id'):
                where_conditions.append("m.league_id = ?")
                params.append(filters['league_id'])
            if filters.get('patch_id'):
                where_conditions.append("l.patch_id = ?")
                params.append(filters['patch_id'])
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Join with league_info to get patch information
        query = f"""
            SELECT m.{metric} 
            FROM match_info m
            JOIN league_info l ON m.league_id = l.league_id
            WHERE {where_clause}
        """
        
        self.cursor.execute(query, params)
        results = self.cursor.fetchall()
        
        if not results:
            return None
        
        values = [row[0] for row in results if row[0] is not None]
        
        if not values:
            return None
        
        # Calculate comprehensive statistics
        stats = {
            'count': len(values),
            'mean': float(np.mean(values)),
            'median': float(np.median(values)),
            'std': float(np.std(values)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'q25': float(np.percentile(values, 25)),
            'q75': float(np.percentile(values, 75))
        }
        
        return stats

    def get_current_patch_id(self):
        """Get the most recent patch ID from the database"""
        self.cursor.execute("""
            SELECT patch_id FROM league_info 
            ORDER BY league_id DESC 
            LIMIT 1
        """)
        result = self.cursor.fetchone()
        return result[0] if result else None
