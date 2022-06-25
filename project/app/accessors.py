from collections.abc import Iterable
from datetime import datetime

from marshmallow import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError

from .database import Database
from .models import Item
from .schemas import ItemType


class ItemAccessor(Database):
    async def import_many(self, items_objects: Iterable[Item]) -> None:
        async with self.session() as db:
            insert_statement = insert(Item).values(
                tuple(item.dict() for item in items_objects)
            )
            try:
                await db.execute(
                    insert_statement.on_conflict_do_update(
                        constraint=Item.__table__.primary_key,
                        set_=insert_statement.excluded,
                    )
                )
            except IntegrityError:
                raise ValidationError('database integrity error')

    async def get(self, item_id: int) -> Item:
        async with self.session() as db:
            return await db.get(Item, item_id)

    async def get_offers_in_date_range(
            self, start: datetime, end: datetime
    ) -> list[Item]:
        async with self.session() as db:
            result: CursorResult = await db.execute(
                select(Item).
                where(Item.type == ItemType.OFFER).
                where(Item.date.between(start, end))
            )
            return result.scalars().all()

    async def delete(self, item_id: int) -> bool:
        async with self.session() as db:
            result: CursorResult = await db.execute(
                delete(Item).where(Item.id == item_id)
            )
            return result.rowcount != 0
