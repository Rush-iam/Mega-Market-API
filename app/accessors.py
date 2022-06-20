import uuid
from collections.abc import Iterable
from datetime import datetime

from marshmallow import ValidationError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload, joinedload

from . import schemas
from .database import Database
from .models import Item


class ItemAccessor(Database):
    async def import_many(self, items: Iterable[Item]):
        async with self.connection() as db:
            insert_statement = insert(Item).values(
                tuple(item.dict() for item in items)
            )
            try:
                await db.execute(
                    insert_statement.on_conflict_do_update(
                        constraint=Item.__table__.primary_key,
                        set_={
                            column.name: column
                            for column in insert_statement.excluded
                            if column.name != 'id'
                        },
                    )
                )
            except IntegrityError:
                await db.rollback()
                raise ValidationError('database integrity error')

            # item = Item(
            #     id=uuid.uuid4().hex,
            #     name="Hello!",
            #     date=datetime.now(),
            #     parent_id=uuid.uuid4().hex,
            #     type="OFFER",
            #     price=None,
            #     children=uuid.uuid4().hex,
            # )
            # session.add(item)

    async def get(self, item_id: int):
        async with self._session_maker() as db:
            # result = await db.execute(select(Item).where(Item.id == item_id)
            #     .options(selectinload(Item.children)))
            # object = result.scalars().first()

            return await db.get(Item, item_id)

    async def delete(self, item_id: int) -> bool:
        async with self.session() as db:
            if item := await db.get(Item, item_id):
                await db.delete(item)
            return item is not None
