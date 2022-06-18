from aiohttp import web
from aiohttp.web_app import Application

from .views import (
    ImportsView,
    DeleteView,
    NodesView,
    SalesView,
    StatisticView,
)


def setup_routes(app: Application):
    app.add_routes([
        web.view('/imports', ImportsView),
        web.view('/delete/{id}', DeleteView),
        web.view('/nodes/{id}', NodesView),
        web.view('/sales', SalesView),
        web.view('/node/{id}/statistic', StatisticView),
    ])
