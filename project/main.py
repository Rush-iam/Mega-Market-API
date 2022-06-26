import logging
import os
from collections import defaultdict
from typing import Any

from aiohttp import web
from aiohttp.web_app import Application
from aiohttp_apispec import setup_aiohttp_apispec
from dotenv import dotenv_values


def get_config() -> dict[str, Any]:
    """
    Returns nested dict of options from .env config file.
    You can override option with an environment variable.

    Example .env file:
        DB_HOST=123
    Returns:
        {'db': {'host': 123}}
    :return:
    """

    config_filename = 'config.env'

    config_env = dotenv_values(os.environ.get('CONFIG_PATH', config_filename))
    if not config_env:
        raise FileNotFoundError(f'missing config file: {config_filename}')

    config = defaultdict(dict)
    for key_name, value in config_env.items():
        if '_' not in key_name:
            continue
        config_category, option = key_name.lower().split('_', 1)
        config[config_category][option] = os.getenv(key_name, value)
    return config


async def app_factory() -> Application:
    """
    Returns runnable aiohttp application,
    that can be passed as an argument to ``aiohttp.web.runapp()``
    """

    from app.routes import setup_routes
    from app.middlewares import setup_middlewares
    from app.store import setup_store

    app: Application = web.Application()
    app['config'] = get_config()
    logging.basicConfig(level=logging.INFO)

    setup_aiohttp_apispec(
        app=app,
        title="Mega Market Open API",
        version="1.0",
        swagger_path="/docs",
    )
    setup_routes(app)
    setup_middlewares(app)
    setup_store(app)

    async def welcome(_): logging.info("Mega Market server started")
    app.on_startup.append(welcome)
    return app


if __name__ == '__main__':
    web.run_app(app_factory(), port=80)
