import uuid
from collections.abc import Iterable
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert

from .database import Database
from .models import Item


class ItemAccessor(Database):
    async def import_many(self, items: Iterable[Item]):
        async with self.connection() as db:
            insert_statement = insert(Item).values(
                tuple(item.dict() for item in items)
            )
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
