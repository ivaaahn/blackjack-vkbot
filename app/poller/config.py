import yaml

from dataclasses import dataclass


@dataclass
class RabbitConfig:
    host: str
    port: int
    user: str
    password: str
    queue_name: str


@dataclass
class BotConfig:
    token: str
    group_id: int


@dataclass
class Config:
    rabbit: RabbitConfig
    bot: BotConfig


def setup_config(config_path: str) -> Config:
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)
        
        config = Config(
            rabbit=RabbitConfig(**raw_config['rabbit']),
            bot=BotConfig(**raw_config['bot']),
        )

    return config
