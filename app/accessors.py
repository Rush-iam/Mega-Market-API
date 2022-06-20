import uuid
from collections.abc import Iterable
from datetime import datetime

from marshmallow import ValidationError
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError

from .database import Database
from .models import Item


class ItemAccessor(Database):
    async def import_many(self, items_objects: Iterable[Item]):
        async with self.session() as db:
            items = [item.dict() for item in items_objects]
            categories = [item for item in items if item['type'] == 'CATEGORY']
            offers = [item for item in items if item['type'] == 'OFFER']

            # Important order: categories first - to check offer parents
            for collection in categories, offers:
                insert_statement = insert(Item).values(collection)
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
        async with self.session() as db:
            return await db.get(Item, item_id)

    async def delete(self, item_id: int) -> bool:
        async with self.session() as db:
            result: CursorResult = await db.execute(
                delete(Item).where(Item.id == item_id)
            )
            return result.rowcount != 0
