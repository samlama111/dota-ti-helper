import time
import requests
from db_utils import insert_match_data, create_db, insert_hero_data


def get_all_ti_matches(league_id):
    return requests.get(
        f"https://api.opendota.com/api/leagues/{league_id}/matches"
    ).json()


def get_match(match_id):
    return requests.get(f"https://api.opendota.com/api/matches/{match_id}?").json()


def get_hero_stats():
    return requests.get("https://api.opendota.com/api/heroStats").json()


def insert_heroes():
    hero_dict = get_hero_stats()
    hero_ids = [hero["id"] for hero in hero_dict]
    hero_names = [hero["localized_name"] for hero in hero_dict]
    # Insert into hero_info table
    for hero_id, hero_name in zip(hero_ids, hero_names):
        insert_hero_data(hero_id, hero_name)


def get_play_lh_at_5mins(match, tournament_id):
    if "players" not in match:
        print(match)  # Prints most likely error
        print("No players in match")
        return

    radiant_lane_1_players = []
    radiant_lane_2_players = []
    radiant_lane_3_players = []
    dire_lane_1_players = []
    dire_lane_2_players = []
    dire_lane_3_players = []
    for player in match["players"]:
        # Populate the lane lists
        if player["lane"] == 1 and player["isRadiant"]:
            radiant_lane_1_players.append(player)
        elif player["lane"] == 2 and player["isRadiant"]:
            radiant_lane_2_players.append(player)
        elif player["lane"] == 3 and player["isRadiant"]:
            radiant_lane_3_players.append(player)
        elif player["lane"] == 1 and not player["isRadiant"]:
            dire_lane_1_players.append(player)
        elif player["lane"] == 2 and not player["isRadiant"]:
            dire_lane_2_players.append(player)
        elif player["lane"] == 3 and not player["isRadiant"]:
            dire_lane_3_players.append(player)

    for player in match["players"]:
        player_name = player["name"] if player["name"] else player["personaname"]
        fallback_name = player_name if player_name else "Saksa, or someone else idk"
        hero_id = player["hero_id"]
        kills = player["hero_kills"]
        if len(player["lh_t"]) < 5:
            print("Game did not last 5 mins")
            continue
        last_hits_at_5 = player["lh_t"][5]

        current_lane = player["lane"]
        is_radiant = player["isRadiant"]
        heroes_on_lane = [
            player["hero_id"]
            for player in match["players"]
            if player["lane"] == current_lane and player["isRadiant"] != is_radiant
        ]

        print(f"At 5 mins, {fallback_name} got {last_hits_at_5} last hits")

        # Insert data into SQLite database
        insert_match_data(
            tournament_id,
            match["match_id"],
            fallback_name,
            hero_id,
            kills,
            last_hits_at_5,
            heroes_on_lane,
        )


# Create the database and table
create_db()

# Insert hero data into hero_info table
insert_heroes()

ti_league_id = "16935"
wallachia_league_id = "17119"
bb_dacha_belgrade_league_id = "17126"
dreamleague_season_24 = "17272"
blast_slam_1 = "17414"
esl_one_bangkok_2024 = "17509"

current_league_id = esl_one_bangkok_2024

for match in get_all_ti_matches(current_league_id):
    print(match["match_id"])
    match_info = get_match(match["match_id"])
    get_play_lh_at_5mins(match_info, current_league_id)
    # Time out for 5s, to avoid getting rate limited
    time.sleep(5)
