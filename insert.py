from opendota_api import (
    get_hero_stats,
    get_league_teams,
)


def insert_heroes(db):
    hero_dict = get_hero_stats()
    hero_ids = [hero["id"] for hero in hero_dict]
    hero_names = [hero["localized_name"] for hero in hero_dict]
    # Insert into hero_info table
    for hero_id, hero_name in zip(hero_ids, hero_names):
        db.insert_hero_data(hero_id, hero_name)


def insert_teams(db, league_id):
    teams = get_league_teams(league_id)
    for team in teams:
        db.insert_team_data(team["team_id"], team["name"])


def create_and_insert_match_data(db, match, tournament_id):
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
            if player["lane"] == current_lane
            and player["isRadiant"] == is_radiant  # and player["hero_id"] != hero_id
        ]
        enemy_heroes_on_lane = [
            player["hero_id"]
            for player in match["players"]
            if player["lane"] == current_lane and player["isRadiant"] != is_radiant
        ]

        team_id = match["radiant_team_id"] if is_radiant else match["dire_team_id"]

        print(f"At 5 mins, {fallback_name} got {last_hits_at_5} last hits")

        # Insert data into SQLite database
        db.insert_match_data(
            tournament_id,
            match["match_id"],
            fallback_name,
            hero_id,
            kills,
            last_hits_at_5,
            heroes_on_lane,
            enemy_heroes_on_lane,
            team_id,
        )
