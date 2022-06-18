from marshmallow import Schema, fields, validate


# TODO enum class type?


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
        required=True,
        nullable=False,
        description='Время последнего обновления элемента',
        example='2022-05-28T21:12:01.000Z',
    )  # TODO: символ T!!! на всех датах
    parent_id = fields.UUID(
        data_key='parentId',
        allow_none=True,
        nullable=True,
        description='UUID родительской категории',
        example='3fa85f64-5717-4562-b3fc-2c963f66a444',
    )
    type = fields.Str(
        required=True,
        validate=validate.OneOf(['OFFER', 'CATEGORY']),
        description='Тип элемента - категория или товар',
    )
    price = fields.Int(
        allow_none=True,
        format='int64',
        nullable=True,
        description=''
        'Целое число, для категории - это средняя цена всех дочерних товаров'
        ' (включая товары подкатегорий).\n'
        'Если цена является не целым числом, округляется в меньшую сторону до'
        ' целого числа. Если категория не содержит товаров цена равна null.\n',
    )
    children = fields.List(
        fields.Nested(lambda: ShopUnit()),
        description=''
        'Список всех дочерних товаров\\категорий. Для товаров поле равно null.'
    )

    class Meta:
        ordered = True


class Id(ShopUnit):
    class Meta:
        fields = ('id', )


class ShopUnitImport(ShopUnit):
    class Meta:
        exclude = ('date', 'children')


class ShopUnitImportRequest(Schema):
    items = fields.List(
        fields.Nested(ShopUnitImport),
        nullable=False,
        description='Импортируемые элементы',
    )
    update_date = fields.AwareDateTime(
        data_key='updateDate',
        nullable=False,
        description='Время обновления добавляемых товаров/категорий',
        example='2022-05-28T21:12:01.000Z',
    )

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
        exclude = ('children', )


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
