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
    attack_types = [hero["attack_type"] for hero in hero_dict]
    primary_attributes = [hero["primary_attr"] for hero in hero_dict]
    base_attack_mins = [hero["base_attack_min"] for hero in hero_dict]
    base_attack_maxs = [hero["base_attack_max"] for hero in hero_dict]
    # Insert into hero_info table
    for hero_id, hero_name, attack_type, primary_attribute, base_attack_min, base_attack_max in zip(hero_ids, hero_names, attack_types, primary_attributes, base_attack_mins, base_attack_maxs):
        db.insert_hero_data(hero_id, hero_name, attack_type, primary_attribute, base_attack_min, base_attack_max)


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
        is_roaming = player["is_roaming"]
        is_radiant = player["isRadiant"]
        lane_role = player["lane_role"]
        # 1 = safelane, 2 = mid, 3 = offlane
        if is_roaming == True:
            print("Occured in match id ", match["match_id"], "for player: ", player["name"], "is roaming")
            lane_role = 4.5 # Set lane role to 4.5 if the player is roaming, as it most likely is a support
        if lane_role == 4:
            print("Occured in match id ", match["match_id"], "for player: ", player["name"], "is jungling/roaming")
            lane_role = 4.5 # Set lane role to 4.5 if the player is jungling/roaming, as it most likely is a support
        if lane_role == 0:
            print("Occured in match id ", match["match_id"], "for player: ", player["name"])
            raise ValueError("Lane role is ", lane_role)
        

        if len(player["lh_t"]) < 5:
            print("Game did not last 5 mins")
            continue
        last_hits_at_5 = player["lh_t"][5]
        denies_at_5 = player["dn_t"][5]

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
        lane_teammate_lh_at_5 = [
            p["lh_t"][5]
            for p in all_players
            if p["lane"] == current_lane and p["isRadiant"] == is_radiant and p["hero_id"] != hero_id
        ]
        lane_teammate_role_and_is_roaming = [
            (p["lane_role"], p["is_roaming"])
            for p in all_players
            if p["lane"] == current_lane and p["isRadiant"] == is_radiant and p["hero_id"] != hero_id
        ]
        is_teammate_roaming = False
        if len(lane_teammate_role_and_is_roaming) > 0:
            is_teammate_roaming = lane_teammate_role_and_is_roaming[0][0] == 4 or lane_teammate_role_and_is_roaming[0][1] == True
        # TODO: Handle trilanes
        if len(lane_teammate_lh_at_5) == 0:
            if lane_role != 2:
                print(f"No lane teammate for {player['name']}, continuing with role {lane_role}")
        else:
            # Change lane_role for safelane if the teammate has more last hits at 5
            # Pos 5 support
            if lane_role == 1 and (lane_teammate_lh_at_5[0] >= last_hits_at_5) and not is_teammate_roaming: # TODO: Test with 8027003149
                lane_role = 5 
            # Roaming support, on mid
            elif lane_role == 2 and (lane_teammate_lh_at_5[0] >= last_hits_at_5) and not is_teammate_roaming:
                lane_role = 4.5
            # Pos 4 support
            elif lane_role == 3 and (lane_teammate_lh_at_5[0] >= last_hits_at_5) and not is_teammate_roaming:
                lane_role = 4

        # Insert data into SQLite database
        db.insert_match_data(
            league_id,
            match["match_id"],
            player["account_id"],
            hero_id,
            kills,
            last_hits_at_5,
            denies_at_5,
            heroes_on_lane,
            enemy_heroes_on_lane,
            lane_role,
            is_roaming,
            is_radiant,
            match["patch"],
        )
