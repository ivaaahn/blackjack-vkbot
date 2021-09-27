import asyncio
import os
import click
from app.app import setup_app
from aiohttp.web import run_app

from app.poller.poller import Poller, run_poller


def run_bot(x):
    pass


@click.command()
@click.option('--service', default='api', help='Choose service to run')
def main(service: str) -> None:
    app = setup_app(os.path.join(os.path.dirname(__file__), 'config.yml'))

    choose = {
        'api': lambda: run_app(app),
        'poller': lambda: run_poller(app),
        'bot': lambda: run_bot(app),
    }

    try:
        choose[service]()
    except KeyError:
        print('service have to be one of: api, poller, bot')


if __name__ == "__main__":
    main()

    # # loop = asyncio.get_event_loop()
    # # poller_task = asyncio.create_task()
    # run_poller(cfg_path)
