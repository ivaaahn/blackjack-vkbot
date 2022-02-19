import os

import click
from aiohttp.web import run_app as run_app_api

from proj.api import (
    create_app as create_app_api,
)
from proj.config import setup_config
from proj.logger import LoggerFactory
from proj.poller import (
    create_app as create_app_poller,
    run_poller as run_app_poller,
)
from proj.core import (
    create_app as create_app_core,
    run_worker as run_app_core,
)


@click.command()
@click.option("--service", default="api", help="Choose service to run")
def main(service: str) -> None:
    config_path = os.path.join(os.path.dirname(__file__), "config.yml")
    config = setup_config(config_path)

    logger_factory = LoggerFactory(config["logging"])

    logger = logger_factory.create("ROOT")

    logger.info(f'Service is "{service}"')

    services = {
        "api": lambda: run_app_api(create_app_api(config.get("api"), logger_factory)),
        "poller": lambda: run_app_poller(
            create_app_poller(config.get("poller"), logger_factory)
        ),
        "worker": lambda: run_app_core(
            create_app_core(config.get("worker"), logger_factory)
        ),
    }

    try:
        chosen_service = services[service]
    except KeyError:
        logger.exception(f"Bad service was received: {service}")
    else:
        logger.debug(f"Service {service} is okay!")
        chosen_service()


if __name__ == "__main__":
    main()
