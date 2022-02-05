from dataclasses import dataclass
from typing import TypeVar

__all__ = ("MongoConfig",)


@dataclass
class MongoCollectionsConfig:
    players: str
    admins: str
    game_settings: str


@dataclass
class MongoConfig:
    host: str
    port: int
    db: str
    user: str
    password: str
    uuidRepresentation: str
    collections: MongoCollectionsConfig
    server_selection_timeout: int
    reconnect_timeout: int


ConfigType = TypeVar("ConfigType", bound=MongoConfig)
