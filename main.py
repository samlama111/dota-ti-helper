import time
from dotenv import load_dotenv

from db_utils import SQLiteDB
from insert import create_and_insert_match_data, insert_heroes, insert_teams_and_their_players
from opendota_api import get_all_league_matches, get_league_info, get_match

load_dotenv()

league_id_kv: dict[str, int | None] = {
    "ti_2024": 16935,
    "wallachia_2_2024": 17119,
    "bb_dacha_belgrade_2024": 17126,
    "dreamleague_season_24": 17272,
    "blast_slam_1_2024": 17414,
    "esl_one_bangkok_2024": 17509,
    "fissure_playground_1_2025": 17588,
    "blast_slam_2_2024": 17417,
    "dreamleague_season_25": 17765,
    "wallachia_3_2025": 17891,
    "fissure_universe_4_2025": 17907,
    "esl_one_raleigh_2025": 17795,
    "wallachia_4_2025": 18058,
    "blast_slam_3_2025": 17418,
    "dreamleague_season_26": 18111,
    "wallachia_5_2025": 18358,
    "esports_world_championship_2025": 18375,
    "clavision_masters_2025": 18359,
    "fissure_universe_6_2025": 18433,
    # To be played
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

        # Get the highest match_id from the database to determine what's already processed
        latest_match_id_in_db = db.get_latest_match_id()
        print(f"Latest match_id in db: {latest_match_id_in_db}")

        # If no matches exist yet, start from 0
        if latest_match_id_in_db is None:
            latest_match_id_in_db = 0

        # Process all leagues, but skip matches that are already in the database
        for current_league_name, current_league_id in league_id_kv.items():
            if current_league_id is None:
                continue

            print(f"Processing league {current_league_name}")

            # Check if we need to process this league at all
            league_matches = get_all_league_matches(current_league_id)
            new_matches = [
                m for m in league_matches if m["match_id"] > latest_match_id_in_db
            ]

            if not new_matches:
                print(f"No new matches for {current_league_name}")
                continue

            print(f"Found {len(new_matches)} new matches for {current_league_name}")

            # Insert team data into team_info table (only if not already present)
            insert_teams_and_their_players(db, current_league_id)
            print(f"Inserted teams and their players for {current_league_name}")

            # Insert league info (only if not already present)
            if not db.league_exists(current_league_id):
                first_match_info = league_matches[0]
                first_match_id = first_match_info["match_id"]
                first_match = get_match(first_match_id)

                league_info = get_league_info(current_league_id)
                db.insert_league_data(
                    current_league_id,
                    league_info["name"],
                    league_info["tier"],
                    first_match["patch"],
                )
                print(f"Inserted league info for {current_league_name}")

            # Process only the new matches
            for match in new_matches:
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
