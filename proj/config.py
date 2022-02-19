from collections import Mapping
from typing import TypeVar

import yaml


def setup_config(config_path: str) -> Mapping:
    with open(config_path, "r") as f:
        raw_config = yaml.full_load(f)

    return raw_config


ConfigType = TypeVar("ConfigType")


# import yaml
# from dataclasses import dataclass
#
#
# @dataclass
# class SessionConfig:
#     key: str
#
#
# @dataclass
# class AdminConfig:
#     email: str
#     password: str
#
#
# @dataclass
# class BotConfig:
#     token: str
#     group_id: int
#
#
# @dataclass
# class RedisConfig:
#     host: str
#     port: int
#     user: str = "redis"
#     password: str = "redis"
#     db: int = 0
#
#
# @dataclass
# class MongoCollections:
#     players: str
#     admins: str
#     game_settings: str
#
#
# @dataclass
# class MongoConfig:
#     host: str
#     port: int
#     db: str
#     user: str
#     password: str
#     uuidRepresentation: str
#     collections: MongoCollections
#
#
# @dataclass
# class RabbitConfig:
#     host: str
#     port: int
#     user: str
#     password: str
#     queue_name: str
#
#
# @dataclass
# class GameConfig:
#     start_cash: float
#     bonus: float
#     bonus_period: int
#     min_bet: float
#     max_bet: float
#     num_of_decks: int
#
#
# @dataclass
# class Config:
#     admin: AdminConfig
#     session: SessionConfig
#     bot: BotConfig
#     mongo: MongoConfig
#     redis: RedisConfig
#     rabbitmq: RabbitConfig
#     game: GameConfig
#
#
# def setup_config(config_path: str) -> Config:
#     with open(config_path, "r") as f:
#         raw_config = yaml.safe_load(f)
#
#     return Config(
#         admin=AdminConfig(
#             email=raw_config["admin"]["email"],
#             password=raw_config["admin"]["password"],
#         ),
#         session=SessionConfig(key=raw_config["session"]["key"]),
#         bot=BotConfig(
#             token=raw_config["bot"]["token"], group_id=raw_config["bot"]["group_id"]
#         ),
#         mongo=MongoConfig(
#             host=raw_config["mongo"]["host"],
#             port=raw_config["mongo"]["port"],
#             db=raw_config["mongo"]["db"],
#             user=raw_config["mongo"]["user"],
#             password=raw_config["mongo"]["password"],
#             uuidRepresentation=raw_config["mongo"]["uuidRepresentation"],
#             collections=MongoCollections(
#                 players=raw_config["mongo"]["collections"]["players"],
#                 admins=raw_config["mongo"]["collections"]["admins"],
#                 game_settings=raw_config["mongo"]["collections"]["game_settings"],
#             ),
#         ),
#         redis=RedisConfig(**raw_config["redis"]),
#         game=GameConfig(**raw_config["game"]),
#         rabbitmq=RabbitConfig(**raw_config["rabbitmq"]),
#     )
