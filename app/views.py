from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Any

from aiohttp.web_exceptions import HTTPNotFound
from aiohttp.web_response import json_response, Response
from aiohttp.web_urldispatcher import View
from aiohttp_apispec import (
    docs, json_schema, querystring_schema, match_info_schema
)

from . import schemas


class ItemNotFound(HTTPNotFound):
    pass


class ImportsView(View):
    @docs(
        tags=['Базовые задачи'],
        description=''
        'Импортирует новые товары и/или категории.\n'
        'Товары/категории импортированные повторно обновляют текущие.\n'
        'Изменение типа элемента с товара на категорию или с категории'
        ' на товар не допускается.\n'
        'Порядок элементов в запросе является произвольным.\n',
        responses={
            200: {
                'description': 'Вставка или обновление прошли успешно',
            },
            400: {
                'schema': schemas.Error,
                'description':
                    'Невалидная схема документа или входные данные не верны',
            }
        }
    )
    @json_schema(
        schemas.ShopUnitImportRequest,
        description='Импортируемые элементы',
    )
    async def post(self) -> Response:
        import_req: Mapping[str, datetime | list[Any]] = self.request['json']
        items = schemas.ShopUnitImportRequest.make_orm_objects(import_req)
        await self.request.app['items'].import_many(items)
        return Response()


class DeleteView(View):
    @docs(
        tags=['Базовые задачи'],
        description=''
        'Удалить элемент по идентификатору.\n'
        'При удалении категории удаляются все дочерние элементы.\n'
        'Доступ к статистике (истории обновлений) удаленного элемента'
        ' невозможен.\n',
        responses={
            200: {
                'description': 'Удаление прошло успешно',
            },
            400: {
                'schema': schemas.Error,
                'description':
                    'Невалидная схема документа или входные данные не верны',
                # TODO examples ???
            },
            404: {
                'schema': schemas.Error,
                'description': 'Категория/товар не найден',
            },
        }
    )
    @match_info_schema(schemas.Id)
    async def delete(self) -> Response:
        item_id = self.request.match_info['id']
        found = await self.request.app['items'].delete(item_id)
        if not found:
            raise ItemNotFound

        return Response()


class NodesView(View):
    @docs(
        tags=['Базовые задачи'],
        description=''
        'Получить информацию об элементе по идентификатору.\n'
        'При получении информации о категории также предоставляется'
        ' информация о её дочерних элементах.\n'
        '\n'
        '- для пустой категории поле children равно пустому массиву, а для'
        ' товара равно null\n'
        '- цена категории - это средняя цена всех её товаров, включая товары'
        ' дочерних категорий. Если категория не содержит товаров цена равна'
        ' null. При обновлении цены товара, средняя цена категории, которая'
        ' содержит этот товар, тоже обновляется.\n',
        responses={
            200: {
                'schema': schemas.ShopUnit,
                'description': 'Информация об элементе',
            },
            400: {
                'schema': schemas.Error,
                'description':
                    'Невалидная схема документа или входные данные не верны',
            },
            404: {
                'schema': schemas.Error,
                'description': 'Категория/товар не найден',
            },
        },
    )
    @match_info_schema(schemas.Id)
    async def get(self) -> Response:
        item_id = self.request.match_info['id']
        item = await self.request.app['items'].get(item_id)
        if item is None:
            raise ItemNotFound

        item.fulfill_category_prices()
        schema = schemas.ShopUnit()
        return json_response(body=schema.dumps(item))


class SalesView(View):
    @docs(
        tags=['Дополнительные задачи'],
        description=''
        'Получение списка **товаров**, цена которых была обновлена за последние'
        ' 24 часа включительно [now() - 24h, now()] от времени переданном в'
        ' запросе.\n',
        responses={
            200: {
                'schema': schemas.ShopUnitStatisticResponse,
                'description': 'Список товаров, цена которых была обновлена',
            },
            400: {
                'schema': schemas.Error,
                'description':
                    'Невалидная схема документа или входные данные не верны',
            },
        }
    )
    @querystring_schema(schemas.Date)
    async def get(self) -> Response:
        date = self.request['querystring']['date']
        offers = await self.request.app['items'].get_offers_in_date_range(
            date - timedelta(days=1), date,
        )
        schema = schemas.ShopUnitStatisticResponse()
        return json_response(body=schema.dumps({'items': offers}))


class StatisticView(View):
    @docs(
        tags=['Дополнительные задачи'],
        description=''
        'Получение статистики (истории обновлений) по товару/категории за'
        ' заданный полуинтервал [from, to).\n'
        'Статистика по удаленным элементам недоступна.\n'
        '- цена категории - это средняя цена всех её товаров, включая товары'
        ' дочерних категорий. Если категория не содержит товаров цена равна'
        ' null. При обновлении цены товара, средняя цена категории, которая'
        ' содержит этот товар, тоже обновляется.\n'
        '- можно получить статистику за всё время.',
        responses={
            200: {
                'schema': schemas.ShopUnitStatisticResponse,
                'description': 'Статистика по элементу',
            },
            400: {
                'schema': schemas.Error,
                'description': 'Некорректный формат запроса '
                               'или некорректные даты интервала',
            },
            404: {
                'schema': schemas.Error,
                'description': 'Категория/товар не найден',
            },
        }
    )
    @match_info_schema(schemas.Id)
    @querystring_schema(schemas.DateStartEnd)
    async def get(self) -> Response:
        item_id = self.request.match_info.get('id')
        return json_response({})  # TODO

