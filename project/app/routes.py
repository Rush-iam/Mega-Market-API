from aiohttp import web
from aiohttp.web_app import Application

from . import views


def setup_routes(app: Application) -> None:
    app.add_routes([
        web.view('/imports', views.ImportsView),
        web.view('/delete/{id}', views.DeleteView),
        web.view('/nodes/{id}', views.NodesView),
        web.view('/sales', views.SalesView),
        web.view('/node/{id}/statistic', views.StatisticView),
    ])
