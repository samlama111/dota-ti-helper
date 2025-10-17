from peewee import fn

from dota_api.opendota_api import (
    get_hero_stats,
    get_league_teams,
    get_team_players,
    get_league_info,
    get_league_matches,
)
from db.models import Hero, Team, Player, League, Match
from db_cache.db_utils import get_or_fetch_match


## Heroes
def _get_hero_name(hero_id: int) -> str:
    return Hero.select(Hero.hero_name).where(Hero.hero_id == hero_id).scalar()


def get_all_heroes():
    return Hero.select(Hero.hero_id, Hero.hero_name)


def insert_heroes():
    hero_dict = get_hero_stats()
    for hero in hero_dict:
        Hero.get_or_create(
            hero_id=hero["id"],
            hero_name=hero["localized_name"],
            attack_type=hero["attack_type"],
            primary_attribute=hero["primary_attr"],
            base_attack_min=hero["base_attack_min"],
            base_attack_max=hero["base_attack_max"],
        )


## Players and teams
def insert_teams_and_their_players(league_id):
    teams = get_league_teams(league_id)
    for team in teams:
        team_exists = (
            Team.select(Team.team_id).where(Team.team_id == team["team_id"]).scalar()
        )
        if team_exists:
            # Update team rating
            Team.update(rating=team["rating"]).where(
                Team.team_id == team["team_id"]
            ).execute()
            continue
        else:
            Team.create(
                team_id=team["team_id"],
                team_name=team["name"],
                rating=team["rating"],
            )
        players = get_team_players(team["team_id"])

        for player in players:
            if not player.get("name"):
                continue
            Player.get_or_create(
                player_account_id=player["account_id"],
                player_name=player.get("name"),
                player_team_id=team["team_id"],
                is_active=player["is_current_team_member"],
            )


def get_all_players():
    return Player.select()


def get_active_players_by_team(team_id: int):
    return Player.select(Player.player_account_id, Player.player_name).where(
        Player.player_team_id == team_id,
        Player.is_active == True,
    )


def get_all_teams():
    return Team.select(Team.team_id, Team.team_name, Team.rating)


## Leagues
def _get_league_patch_id(league_id: int) -> int:
    league_matches = get_league_matches(league_id)
    first_match_info = league_matches[0]
    first_match_id = first_match_info["match_id"]
    first_match = get_or_fetch_match(first_match_id)
    return first_match["patch"]


def insert_league_info(league_id: int, league_name: str):
    current_league_count = (
        League.select(fn.COUNT()).where(League.league_id == league_id).scalar()
    )
    if current_league_count == 0:
        league_patch_id = _get_league_patch_id(league_id)
        league_info = get_league_info(league_id)
        League.create(
            league_id=league_id,
            league_name=league_info["name"],
            tier=league_info["tier"],
            patch_id=league_patch_id,
        )
        print(f"Inserted league info for {league_name}")


def get_all_leagues():
    return League.select()


# Matches
def get_all_league_matches(league_id: int) -> list[int]:
    return Match.select(Match.match_id).where(Match.league_id == league_id)


def _determine_lane_role(player: dict, match: dict) -> float:
    """Determine the correct lane role for a player."""
    lane_role = player["lane_role"]
    is_roaming = player["is_roaming"]

    # Handle roaming players
    if is_roaming or lane_role == 4:
        print(
            f"Player {player['name']} in match {match['match_id']} is roaming/jungling"
        )
        return 4.5

    # Validate lane role
    if lane_role == 0:
        raise ValueError(f"Invalid lane role 0 for player {player['name']}")

    return lane_role


def _get_lane_context(player: dict, all_players: list) -> dict:
    """Get lane context including friendly and enemy heroes."""
    current_lane = player["lane"]
    is_radiant = player["isRadiant"]
    hero_id = player["hero_id"]

    # Filter players on the same lane
    lane_players = [p for p in all_players if p["lane"] == current_lane]

    friendly_hero_ids = [
        p["hero_id"] for p in lane_players if p["isRadiant"] == is_radiant
    ]
    enemy_hero_ids = [
        p["hero_id"] for p in lane_players if p["isRadiant"] != is_radiant
    ]

    friendly_heroes = [_get_hero_name(hero_id) for hero_id in friendly_hero_ids]
    enemy_heroes = [_get_hero_name(hero_id) for hero_id in enemy_hero_ids]

    return {
        "friendly_heroes_str": ", ".join(friendly_heroes),
        "enemy_heroes_str": ", ".join(enemy_heroes),
        "lane_teammates": [
            p
            for p in lane_players
            if p["isRadiant"] == is_radiant and p["hero_id"] != hero_id
        ],
    }


def _adjust_lane_role_for_support(player_data: dict, lane_context: dict) -> float:
    """Adjust lane role based on last hits comparison with teammates."""
    lane_role = player_data["lane_role"]
    last_hits_at_5 = player_data["last_hits_at_5"]
    player_name = player_data.get("name", "unknown")

    teammates = lane_context["lane_teammates"]

    # Handle case with no teammates (like mid lane)
    if not teammates:
        if lane_role != 2:  # Not mid lane
            print(
                f"No lane teammate for {player_name}, continuing with role {lane_role}"
            )
        return lane_role

    # Get teammate data
    teammate = teammates[0]
    teammate_lh_at_5 = teammate["lh_t"][5]
    teammate_role = teammate["lane_role"]
    is_teammate_roaming = teammate["is_roaming"] or teammate_role == 4

    # If teammate is roaming, don't adjust
    if is_teammate_roaming:
        return lane_role

    # Change to support if lower number of last hits
    if teammate_lh_at_5 >= last_hits_at_5:
        if lane_role == 1:  # Safelane
            return 5  # Pos 5 support
        elif lane_role == 2:  # Mid
            return 4.5  # Roaming support
        elif lane_role == 3:  # Offlane
            return 4  # Pos 4 support

    return lane_role


def _process_player_data(player: dict, match: dict) -> dict:
    """Extract and process player data from match."""
    # Early validation
    if len(player.get("lh_t", [])) < 6:  # Need index 5
        print(f"Game did not last 5 mins for player {player.get('name', 'unknown')}")
        return None

    # Extract basic data
    hero_id = player["hero_id"]
    is_radiant = player["isRadiant"]
    lane_role = _determine_lane_role(player, match)

    if lane_role is None:
        return None

    # Get lane context
    lane_context = _get_lane_context(player, match["players"])

    # Create initial player data
    player_data = {
        "account_id": player["account_id"],
        "hero_id": hero_id,
        "kills": player["hero_kills"],
        "last_hits_at_5": player["lh_t"][5],
        "denies_at_5": player["dn_t"][5],
        "lane_role": lane_role,  # This will be adjusted
        "is_roaming": player["is_roaming"],
        "is_radiant": is_radiant,
        "name": player.get("name", "unknown"),  # Add name for logging
    }

    # Apply the complex lane role adjustments
    adjusted_lane_role = _adjust_lane_role_for_support(player_data, lane_context)
    player_data["assumed_lane_role"] = adjusted_lane_role

    return {
        "account_id": player_data["account_id"],
        "hero_id": player_data["hero_id"],
        "kills": player_data["kills"],
        "last_hits_at_5": player_data["last_hits_at_5"],
        "denies_at_5": player_data["denies_at_5"],
        "heroes_on_lane": lane_context["friendly_heroes_str"],
        "enemy_heroes_on_lane": lane_context["enemy_heroes_str"],
        "assumed_lane_role": adjusted_lane_role,  # Use the adjusted role
        "is_roaming": player_data["is_roaming"],
        "is_radiant": player_data["is_radiant"],
    }


def create_and_insert_match_data(match: dict, league_id: int):
    """Process and insert match data for all players in a match."""
    if "players" not in match:
        print(f"Error: No players in match {match.get('match_id', 'unknown')}")
        return

    for player in match["players"]:
        try:
            processed_player = _process_player_data(player, match)
            if processed_player:
                Match.create(
                    league_id=league_id,
                    match_id=match["match_id"],
                    player_account_id=processed_player["account_id"],
                    hero_id=processed_player["hero_id"],
                    kills=processed_player["kills"],
                    last_hits_at_5=processed_player["last_hits_at_5"],
                    denies_at_5=processed_player["denies_at_5"],
                    heroes_on_lane=processed_player["heroes_on_lane"],
                    enemy_heroes_on_lane=processed_player["enemy_heroes_on_lane"],
                    assumed_lane_role=processed_player["assumed_lane_role"],
                    is_roaming=processed_player["is_roaming"],
                    is_radiant=processed_player["is_radiant"],
                    patch_id=match["patch"],
                )
        except Exception as e:
            print(f"Error processing player {player.get('name', 'unknown')}: {e}")
            continue


def get_relevant_matches(
    player_id: int | None = None,
    hero_id: int | None = None,
    ally_hero_name: str | None = None,
    opponent_hero_name: str | None = None,
    # team_id: int = None,
    lane_role: int | None = None,
    patch_id: int | None = None,
    league_id: int | None = None,
):
    query = Match.select()
    if player_id is not None:
        query = query.where(Match.player_account_id == player_id)
    if hero_id is not None:
        query = query.where(Match.hero_id == hero_id)
    if lane_role is not None:
        query = query.where(Match.assumed_lane_role == lane_role)
    if patch_id is not None:
        query = query.where(Match.patch_id == patch_id)
    if league_id is not None:
        query = query.where(Match.league_id == league_id)
    if opponent_hero_name is not None:
        query = query.where(Match.enemy_heroes_on_lane.contains(opponent_hero_name))
    if ally_hero_name is not None:
        query = query.where(Match.heroes_on_lane.contains(ally_hero_name))
    return query.execute()
