import time
from db.db_utils import (
    create_and_insert_match_data,
    insert_teams_and_their_players,
    insert_league_info,
)
from opendota_api import get_all_league_matches, get_match


def _get_missing_matches(latest_match_id_in_db: int, league_id: int) -> list[int]:
    league_matches = get_all_league_matches(league_id)
    return [m for m in league_matches if m["match_id"] > latest_match_id_in_db]


def insert_all_league_matches(
    latest_match_id_in_db: int, league_id_kv: dict[str, int | None]
):
    # Process all leagues, but skip matches that are already in the database
    for current_league_name, current_league_id in league_id_kv.items():
        if current_league_id is None:
            continue

        print(f"Processing league {current_league_name}")

        # Check if we need to process this league at all
        new_matches = _get_missing_matches(latest_match_id_in_db, current_league_id)

        if not new_matches:
            print(f"No new matches for {current_league_name}")
            continue

        print(f"Found {len(new_matches)} new matches for {current_league_name}")

        # Insert team data into team_info table (only if not already present)
        insert_teams_and_their_players(current_league_id)
        print(f"Inserted teams and their players for {current_league_name}")

        # Insert league info (only if not already present)
        insert_league_info(current_league_id, current_league_name)

        # Process only the new matches
        for match in new_matches:
            match_info = get_match(match["match_id"])
            create_and_insert_match_data(match_info, current_league_id)
            # Time out for 5s, to avoid getting rate limited
            time.sleep(5)
