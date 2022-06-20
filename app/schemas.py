from collections.abc import Generator, Mapping
from datetime import datetime
from typing import Any, MutableMapping

from marshmallow import Schema, fields, validate, post_load, pre_dump, validates_schema, ValidationError, post_dump

from .models import Item

# TODO enum class для type?
# TODO родителем товара или категории может быть только категория


class ShopUnit(Schema):
    id = fields.UUID(
        required=True,
        nullable=False,
        description='Уникальный идентификатор',
        example='3fa85f64-5717-4562-b3fc-2c963f66a333',
    )
    name = fields.Str(
        required=True,
        nullable=False,
        description='Имя категории',
    )
    date = fields.AwareDateTime(
        format='%Y-%m-%dT%H:%M:%S.000Z',
        required=True,
        nullable=False,
        description='Время последнего обновления элемента',
        example='2022-05-28T21:12:01.000Z',
    )
    parent_id = fields.UUID(
        data_key='parentId',
        allow_none=True,
        nullable=True,
        description='UUID родительской категории',
        example='3fa85f64-5717-4562-b3fc-2c963f66a444',
    )
    type = fields.Str(
        validate=validate.OneOf(['OFFER', 'CATEGORY']),
        required=True,
        description='Тип элемента - категория или товар',
    )
    price = fields.Int(
        validate=validate.Range(min=0, max=2**63, max_inclusive=False),
        format='int64',
        allow_none=True,
        nullable=True,
        description=''
        'Целое число, для категории - это средняя цена всех дочерних товаров'
        ' (включая товары подкатегорий).\n'
        'Если цена является не целым числом, округляется в меньшую сторону до'
        ' целого числа. Если категория не содержит товаров цена равна null.\n',
    )
    children = fields.List(
        fields.Nested(lambda: ShopUnit()),
        nullable=True,
        description=''
        'Список всех дочерних товаров\\категорий. Для товаров поле равно null.'
    )

    @validates_schema
    def validate_category_price_is_null(self, data: Mapping[str, Any], **_):
        if data.get('type') == 'CATEGORY' and data.get('price') is not None:
            raise ValidationError('category price must be null')

    @validates_schema
    def validate_offer_price_is_not_null(self, data: Mapping[str, Any], **_):
        if data.get('type') == 'OFFER' and data.get('price') is None:
            raise ValidationError('offer price must be not null')

    @post_dump
    def offer_null_children(
            self, item: MutableMapping[str, Any], **_
    ) -> Mapping[str, Any]:
        if item['type'] == 'OFFER':
            item['children'] = None
        return item

    class Meta:
        ordered = True
        dump_only = ('children',)


class Id(ShopUnit):
    class Meta:
        fields = ('id',)


class ShopUnitImport(ShopUnit):
    class Meta:
        exclude = ('date', 'children')


class ShopUnitImportRequest(Schema):
    items = fields.List(
        fields.Nested(ShopUnitImport),
        required=True,
        nullable=False,
        description='Импортируемые элементы',
    )
    update_date = fields.AwareDateTime(
        data_key='updateDate',
        required=True,
        nullable=False,
        description='Время обновления добавляемых товаров/категорий',
        example='2022-05-28T21:12:01.000Z',
    )

    @validates_schema
    def validate_unique_ids(self, data, **_):
        if len(data['items']) != len(set(item['id'] for item in data['items'])):
            raise ValidationError('multiple items with same id')

    @staticmethod
    def make_orm_objects(
            data: Mapping[str, datetime | list[Any]], **_
    ) -> Generator[Item]:
        date = data['update_date']
        return (Item(date=date, **item_dict) for item_dict in data['items'])

    class Meta:
        ordered = True


class Date(Schema):
    date = fields.AwareDateTime(
        required=True,
        description='Дата и время запроса (ISO 8601)',
        example='2022-05-28T21:12:01.000Z',
    )


class DateStartEnd(Schema):
    date_start = fields.AwareDateTime(
        data_key='dateStart',
        description=''
        'Дата и время начала интервала, для которого считается статистика',
        example='2022-05-28T21:12:01.000Z',
    )
    date_end = fields.AwareDateTime(
        data_key='dateEnd',
        description=''
        'Дата и время конца интервала, для которого считается статистика',
        example='2022-05-28T21:12:01.000Z',
    )

    class Meta:
        ordered = True


class ShopUnitStatisticUnit(ShopUnit):
    class Meta:
        exclude = ('children',)


class ShopUnitStatisticResponse(Schema):
    items = fields.List(
        fields.Nested(ShopUnitStatisticUnit),
        description='История в произвольном порядке',
    )


class Error(Schema):
    code = fields.Integer(required=True, nullable=False)
    message = fields.String(required=True, nullable=False)

    class Meta:
        ordered = True
