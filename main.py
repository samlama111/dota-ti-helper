import time
from dotenv import load_dotenv

from db_utils import SQLiteDB
from insert import create_and_insert_match_data, insert_heroes, insert_teams
from opendota_api import get_all_league_matches, get_league_info, get_match

load_dotenv()

league_id_kv = {
    "ti_2024": "16935",
    "wallachia_2_2024": "17119",
    "bb_dacha_belgrade_2024": "17126",
    "dreamleague_season_24": "17272",
    "blast_slam_1_2024": "17414",
    "esl_one_bangkok_2024": "17509",
    "fissure_playground_1_2025": "17588",
    "blast_slam_2_2024": "17417",
    "dreamleague_season_25": "17765",
    "wallachia_3_2025": "17891",
    # TODO: Find IDs
    "fissure_universe_4_2025": None,
    "esl_one_raleigh_2025": None,
    "wallachia_4_2025": None,
    "blast_slam_3_2025": None,
    "dreamleague_season_26": None,
    "wallachia_5_2025": None,
    "esports_world_championship_2025": None,
    "clavision_masters_2025": None,
    # To be played
    "fissure_universe_6_2025": None,
    "ti_2025": None,
}


def main():
    # file_path_prefix = "old_data/"
    file_path_prefix = "new_data/"
    file_path = file_path_prefix + "dota_2_data_2025_08_19.db"
    db = SQLiteDB(file_path)
    # db = PostgresDB(supabase_url=os.getenv("SUPABASE_URL"), supabase_key=os.getenv("SUPABASE_KEY"))
    try:
        # Create the database and table
        db.create_db()
        # Insert hero data into hero_info table
        insert_heroes(db)

        # TODO: Add a loop to insert all leagues
        current_league_id = league_id_kv["wallachia_3_2025"]

        # Insert team data into team_info table
        insert_teams(db, current_league_id)

        # Insert league info
        first_match_info = get_all_league_matches(current_league_id)[0]
        first_match_id = first_match_info["match_id"]
        first_match = get_match(first_match_id)

        league_info = get_league_info(current_league_id)
        db.insert_league_data(
            current_league_id,
            league_info["name"],
            league_info["tier"],
            first_match["patch"],
        )

        for match in get_all_league_matches(current_league_id):
            print(match["match_id"])
            match_info = get_match(match["match_id"])
            create_and_insert_match_data(db, match_info, current_league_id)
            # Time out for 5s, to avoid getting rate limited
            time.sleep(5)
    except Exception as e:
        print(e)
    finally:
        db.close()


if __name__ == "__main__":
    main()
