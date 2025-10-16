from peewee import (
    Model,
    IntegerField,
    CharField,
    BooleanField,
    CompositeKey,
    FloatField,
)

from db.db_connection import db

# TODO: New attributes
# - match (stage, series_game)

# Not available in the API:
# - player (position, team_role)

# New view (inference-time, not stored in db)
# - player_hero_games, player_hero_avg_lh_5, player_hero_std_lh_5, player_hero_avg_kills


class BaseModel(Model):
    class Meta:
        database = db


# TODO: Add roles
class Hero(BaseModel):
    hero_id = IntegerField(primary_key=True)
    hero_name = CharField()
    attack_type = CharField()
    primary_attribute = CharField()
    base_attack_min = IntegerField()
    base_attack_max = IntegerField()


class League(BaseModel):
    league_id = IntegerField(primary_key=True)
    league_name = CharField()
    tier = CharField()
    patch_id = IntegerField()


class Team(BaseModel):
    team_id = IntegerField(primary_key=True)
    team_name = CharField()
    rating = IntegerField()


class Player(BaseModel):
    player_account_id = IntegerField()
    player_name = CharField()
    player_team_id = IntegerField()
    is_active = BooleanField()

    class Meta:
        primary_key = CompositeKey("player_account_id", "player_team_id")


class Match(BaseModel):
    league_id = IntegerField()
    match_id = IntegerField()
    player_account_id = IntegerField()
    hero_id = IntegerField()
    kills = IntegerField()
    last_hits_at_5 = IntegerField()
    denies_at_5 = IntegerField()
    heroes_on_lane = CharField()
    enemy_heroes_on_lane = CharField()
    assumed_lane_role = FloatField()
    is_roaming = BooleanField()
    is_radiant = BooleanField()
    patch_id = IntegerField()

    class Meta:
        primary_key = CompositeKey("match_id", "player_account_id")
