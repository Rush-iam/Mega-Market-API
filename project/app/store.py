from aiohttp.web_app import Application

from .accessors import ItemAccessor
from .database import Database


def setup_store(app: Application) -> None:
    app.on_startup.append(Database.connect)
    app.on_cleanup.append(Database.disconnect)

    app['items'] = ItemAccessor()
