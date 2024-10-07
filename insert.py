import time
import requests
from db_utils import insert_match_data, create_db, insert_hero_data


def get_all_ti_matches():
    ti_league_id = "16935"
    return requests.get(
        f"https://api.opendota.com/api/leagues/{ti_league_id}/matches"
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


def get_play_lh_at_5mins(match):
    if "players" not in match:
        print(match)  # Prints most likely error
        print("No players in match")
        return
    for player in match["players"]:
        player_name = player["name"] if "name" in player else player["personaname"]
        fallback_name = player_name if player_name else "Saksa, or someone else idk"
        hero_id = player["hero_id"]
        kills = player["hero_kills"]
        if len(player["lh_t"]) < 5:
            print("Game did not last 5 mins")
            continue
        last_hits_at_5 = player["lh_t"][5]

        print(f"At 5 mins, {fallback_name} got {last_hits_at_5} last hits")

        # Insert data into SQLite database
        insert_match_data(
            match["match_id"], fallback_name, hero_id, kills, last_hits_at_5
        )


# Create the database and table
create_db()

# Insert hero data into hero_info table
insert_heroes()

for match in get_all_ti_matches():
    print(match["match_id"])
    match_info = get_match(match["match_id"])
    get_play_lh_at_5mins(match_info)
    # Time out for 5s, to avoid getting rate limited
    time.sleep(5)
