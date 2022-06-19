from aiohttp.web_app import Application


from .accessor import ItemAccessor
from .database import Database


def setup_store(app: Application):
    app.on_startup.append(Database.connect)
    app.on_shutdown.append(Database.disconnect)

    app['items'] = ItemAccessor()
