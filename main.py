from aiohttp import web
from aiohttp_apispec import setup_aiohttp_apispec

from app.routes import setup_routes
from app.middlewares import setup_middlewares
from app.store import setup_store

app = web.Application()

app['config'] = {  # TODO config file or envs
    'db': {
        'database': 'mega_market',
        'username': 'postgres',
        'password': 'j3qq4',
        'host': 'localhost',
    }
}

setup_aiohttp_apispec(
    app=app,
    title="Mega Market Open API",
    version="1.0",
    swagger_path="/docs",
)
setup_routes(app)
setup_middlewares(app)
setup_store(app)

if __name__ == '__main__':
    web.run_app(app, port=80)
