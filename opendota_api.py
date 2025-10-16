import requests


def get_league_matches(league_id):
    return requests.get(
        f"https://api.opendota.com/api/leagues/{league_id}/matches"
    ).json()


def get_match(match_id):
    return requests.get(f"https://api.opendota.com/api/matches/{match_id}?").json()


def get_hero_stats():
    return requests.get("https://api.opendota.com/api/heroStats").json()


def get_league_info(league_id):
    return requests.get(f"https://api.opendota.com/api/leagues/{league_id}").json()


def get_league_teams(league_id):
    return requests.get(
        f"https://api.opendota.com/api/leagues/{league_id}/teams"
    ).json()


def get_team_players(team_id):
    return requests.get(f"https://api.opendota.com/api/teams/{team_id}/players").json()
