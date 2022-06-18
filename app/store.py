from aiohttp.web_app import Application


from .accessor import ItemAccessor
from .database import Database


def setup_store(app: Application):
    db = Database(app['config']['db'])
    app.on_shutdown.append(db.disconnect)

    app['db'] = db
    app['items'] = ItemAccessor(db)
