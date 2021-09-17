import typing
from dataclasses import dataclass

import yaml

if typing.TYPE_CHECKING:
    from app.web.app import Application


@dataclass
class SessionConfig:
    key: str


@dataclass
class AdminConfig:
    email: str
    password: str


@dataclass
class BotConfig:
    token: str
    group_id: int


@dataclass
class RedisConfig:
    host: str = "localhost"
    port: int = 6379
    user: str = "redis"
    password: str = "redis"
    db: int = 0


@dataclass
class MongoCollections:
    players: str
    admins: str


@dataclass
class MongoConfig:
    host: str
    port: int
    db: str
    user: str
    password: str
    uuidRepresentation: str
    collections: MongoCollections


@dataclass
class Config:
    admin: AdminConfig
    session: SessionConfig
    bot: BotConfig
    mongo: MongoConfig
    # database: DatabaseConfig
    redis: RedisConfig


def setup_config(app: "Application", config_path: str):
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    app.config = Config(
        admin=AdminConfig(
            email=raw_config["admin"]["email"],
            password=raw_config["admin"]["password"],
        ),
        session=SessionConfig(
            key=raw_config['session']['key']
        ),
        bot=BotConfig(
            token=raw_config['bot']['token'],
            group_id=raw_config['bot']['group_id']
        ),
        mongo=MongoConfig(
            host=raw_config['mongo']['host'],
            port=raw_config['mongo']['port'],
            db=raw_config['mongo']['db'],
            user=raw_config['mongo']['user'],
            password=raw_config['mongo']['password'],
            uuidRepresentation=raw_config['mongo']['uuidRepresentation'],
            collections=MongoCollections(
                players=raw_config['mongo']['collections']['players'],
                admins=raw_config['mongo']['collections']['admins'],
            ),
        ),
        redis=RedisConfig(**raw_config['redis']),
    )
