from db_utils import BaseDB
from opendota_api import (
    get_hero_stats,
    get_league_teams,
    get_team_players,
)


def insert_heroes(db):
    hero_dict = get_hero_stats()
    hero_ids = [hero["id"] for hero in hero_dict]
    hero_names = [hero["localized_name"] for hero in hero_dict]
    # Insert into hero_info table
    for hero_id, hero_name in zip(hero_ids, hero_names):
        db.insert_hero_data(hero_id, hero_name)


def insert_teams_and_their_players(db, league_id):
    teams = get_league_teams(league_id)
    for team in teams:
        db.insert_team_data(team["team_id"], team["name"], team["rating"])
        players = get_team_players(team["team_id"])
        
        active_players = [player for player in players if player["is_current_team_member"]]
        for player in active_players:
            player_name = player["name"] if player["name"] else player["personaname"]
            fallback_name = player_name if player_name else "Saksa, or someone else idk"
            db.insert_player_data(player["account_id"], fallback_name, team["team_id"])


def create_and_insert_match_data(db: BaseDB, match: dict, league_id: int):
    if "players" not in match:
        print(match)  # Prints most likely error
        print("No players in match")
        return

    for player in match["players"]:
        hero_id = player["hero_id"]
        kills = player["hero_kills"]
        current_lane = player["lane"]
        is_radiant = player["isRadiant"]

        if len(player["lh_t"]) < 5:
            print("Game did not last 5 mins")
            continue
        last_hits_at_5 = player["lh_t"][5]

        all_players = match["players"]
        heroes_on_lane = [
            p["hero_id"]
            for p in all_players
            if p["lane"] == current_lane and p["isRadiant"] == is_radiant
        ]
        enemy_heroes_on_lane = [
            p["hero_id"]
            for p in all_players
            if p["lane"] == current_lane and p["isRadiant"] != is_radiant
        ]

        # print(f"At 5 mins, {fallback_name} got {last_hits_at_5} last hits")

        # Insert data into SQLite database
        db.insert_match_data(
            league_id,
            match["match_id"],
            player["account_id"],
            hero_id,
            kills,
            last_hits_at_5,
            heroes_on_lane,
            enemy_heroes_on_lane,
            is_radiant,
        )
