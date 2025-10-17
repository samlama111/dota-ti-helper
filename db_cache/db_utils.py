from dota_api.opendota_api import get_match
from db_cache.models import ApiCache


def get_or_fetch_match(match_id: int) -> dict | None:
    endpoint = f"https://api.opendota.com/api/matches/{match_id}?"
    match = get_api_cache(endpoint)
    if match:
        return match
    match = get_match(match_id)
    set_api_cache(endpoint, match)
    return match


# API Cache
def get_api_cache(endpoint: str) -> dict | None:
    return (
        ApiCache.select(ApiCache.response_data)
        .where(ApiCache.endpoint == endpoint)
        .scalar()
    )


def set_api_cache(endpoint: str, response_data: dict):
    ApiCache.create(endpoint=endpoint, response_data=response_data)
