import os
from typing import Any

import yaml
from aiohttp import web
from aiohttp.web_app import Application
from aiohttp_apispec import setup_aiohttp_apispec


def get_config() -> dict[str, Any]:
    with open(os.environ.get("CONFIG_PATH", "config.yml")) as file:
        return yaml.safe_load(file)


async def app_factory() -> Application:
    from app.routes import setup_routes
    from app.middlewares import setup_middlewares
    from app.store import setup_store

    app = web.Application()
    app['config'] = get_config()

    setup_aiohttp_apispec(
        app=app,
        title="Mega Market Open API",
        version="1.0",
        swagger_path="/docs",
    )
    setup_routes(app)
    setup_middlewares(app)
    setup_store(app)

    return app


if __name__ == '__main__':
    web.run_app(app_factory(), port=80)
