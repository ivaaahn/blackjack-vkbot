import os
from logging import getLogger
from typing import Mapping

import click

import yaml

from proj.services.api import (
    ApiApplication,
    create_app as create_app_api,
)
from proj.services.app_logger import get_logger
from proj.services.poller import (
    PollerApplication,
    create_app as create_app_poller,
    run_poller as run_app_poller,
)

from proj.services.worker import (
    WorkerApplication,
    create_app as create_app_worker,
    run_worker as run_app_worker,
)

from aiohttp.web import run_app as run_app_api


logger = get_logger(__file__)


def setup_config() -> Mapping:
    config_path = os.path.join(os.path.dirname(__file__), "config.yml")

    with open(config_path, "r") as f:
        raw_config = yaml.full_load(f)

    return raw_config
    #
    # return Config(
    #     admin=AdminConfig(
    #         email=raw_config["admin"]["email"],
    #         password=raw_config["admin"]["password"],
    #     ),
    #     session=SessionConfig(key=raw_config["session"]["key"]),
    #     bot=BotConfig(
    #         token=raw_config["bot"]["token"], group_id=raw_config["bot"]["group_id"]
    #     ),
    #     mongo=MongoConfig(
    #         host=raw_config["mongo"]["host"],
    #         port=raw_config["mongo"]["port"],
    #         db=raw_config["mongo"]["db"],
    #         user=raw_config["mongo"]["user"],
    #         password=raw_config["mongo"]["password"],
    #         uuidRepresentation=raw_config["mongo"]["uuidRepresentation"],
    #         collections=MongoCollections(
    #             players=raw_config["mongo"]["collections"]["players"],
    #             admins=raw_config["mongo"]["collections"]["admins"],
    #             game_settings=raw_config["mongo"]["collections"]["game_settings"],
    #         ),
    #     ),
    #     redis=RedisConfig(**raw_config["redis"]),
    #     game=GameConfig(**raw_config["game"]),
    #     rabbit=RabbitConfig(**raw_config["rabbit"]),
    # )


@click.command()
@click.option("--service", default="poller", help="Choose service to run")
def main(service: str) -> None:
    logger.info(f'Service is "{service}"')

    config = setup_config()

    services = {
        "api": lambda: run_app_api(create_app_api(config.get("api"))),
        "poller": lambda: run_app_poller(create_app_poller(config.get("poller"))),
        "worker": lambda: run_app_worker(create_app_worker(config.get("worker"))),
    }

    try:
        chosen_service = services[service]
    except KeyError:
        logger.exception(f"Bad service was received: {service}")
    else:
        logger.info(f"Service {service} is okay!")
        chosen_service()


if __name__ == "__main__":
    main()
