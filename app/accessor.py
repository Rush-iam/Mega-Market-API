import uuid
from datetime import datetime

from .database import Database
from .models import Item


class ItemAccessor:
    def __init__(self, db: Database):
        self.db = db

    async def import_items(self, items: list[Item]):
        async with self.db.session.begin() as session:
            item = Item(
                id=uuid.uuid4().hex,
                name="Hello!",
                date=datetime.now(),
                parent_id=uuid.uuid4().hex,
                type="OFFER",
                price=None,
                children=uuid.uuid4().hex,
            )
            session.add(item)
