import os
import click
from app.app import setup_app
from aiohttp.web import run_app

from app.worker.worker import setup_worker, run_worker
from app.poller.poller import run_poller, setup_poller

from app.app_logger import get_logger

logger = get_logger(__file__)


@click.command()
@click.option("--service", default="poller", help="Choose service to run")
def main(service: str) -> None:
    logger.info(f'Service is "{service}"')
    cfg_path = os.path.join(os.path.dirname(__file__), "config.yml")

    choose = {
        "api": lambda: run_app(setup_app(cfg_path)),
        "poller": lambda: run_poller(setup_poller(cfg_path)),
        "worker": lambda: run_worker(setup_worker(cfg_path)),
    }

    try:
        func = choose[service]
    except KeyError:
        logger.exception(f"Bad service was received: {service}")
    else:
        logger.info("Service is okay!")
        func()


if __name__ == "__main__":
    main()
