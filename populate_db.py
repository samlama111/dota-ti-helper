from dotenv import load_dotenv

from insert import insert_all_league_matches
from db.db_connection import db
from db.db_models import Hero, League, Team, Player, Match
from db.db_utils import insert_heroes, get_latest_match_id_in_db

load_dotenv()

league_id_kv: dict[str, int | None] = {
    "ti_2025": 18324,
    "fissure_universe_6_2025": 18433,
    "clavision_masters_2025": 18359,
    "esports_world_championship_2025": 18375,
    "wallachia_5_2025": 18358,
    "dreamleague_season_26": 18111,
    "blast_slam_3_2025": 17418,
    "wallachia_4_2025": 18058,
    "esl_one_raleigh_2025": 17795,
    "fissure_universe_4_2025": 17907,
    "wallachia_3_2025": 17891,
    "dreamleague_season_25": 17765,
    "blast_slam_2_2024": 17417,
    "fissure_playground_1_2025": 17588,
    "esl_one_bangkok_2024": 17509,
    "blast_slam_1_2024": 17414,
    "dreamleague_season_24": 17272,
    "bb_dacha_belgrade_2024": 17126,
    "wallachia_2_2024": 17119,
    "ti_2024": 16935,
}


def main():
    try:
        # Create the database and tables
        db.connect()
        db.create_tables([Hero, League, Team, Player, Match])

        # Get the highest match_id from the database to determine what's already processed
        latest_match_id_in_db = get_latest_match_id_in_db()
        print(f"Latest match_id in db: {latest_match_id_in_db}")

        # If no matches exist yet, insert hero data
        if latest_match_id_in_db == 0:
            insert_heroes()

        insert_all_league_matches(latest_match_id_in_db, league_id_kv)

    except Exception as e:
        print(e)
    finally:
        db.close()


if __name__ == "__main__":
    main()
