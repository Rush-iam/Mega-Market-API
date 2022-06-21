from collections.abc import Mapping
from enum import Enum
from typing import Any

from sqlalchemy import (
    Column, CheckConstraint, ForeignKey, BigInteger, String, TIMESTAMP, event, orm
)
from sqlalchemy.dialects.postgresql import UUID

Base = orm.declarative_base()


class ItemType(str, Enum):
    CATEGORY = 'CATEGORY'
    OFFER = 'OFFER'


class Item(Base):
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    date = Column(TIMESTAMP(timezone=True), nullable=False)
    parent_id: str | None = Column(
        UUID(as_uuid=True), ForeignKey(id, ondelete='CASCADE'), index=True,
    )
    type = Column(
        String,
        CheckConstraint(f"type in ('{ItemType.OFFER}', '{ItemType.CATEGORY}')")
    )
    price: int | None = Column(BigInteger, CheckConstraint('price >= 0'))

    children = orm.relationship(
        lambda: Item,
        cascade='save-update, merge, expunge, delete',
        passive_deletes=True,
    )

    __tablename__ = 'items'
    __table_args__ = (
        CheckConstraint(
            f"type != '{ItemType.CATEGORY}' OR price IS NULL",
            name='category_price_is_null',
        ),
        CheckConstraint(
            f"type != '{ItemType.OFFER}' OR price IS NOT NULL",
            name='offer_price_is_not_null',
        ),
    )

    def __repr__(self) -> str:
        return f'Item({self.type}, {self.name}, {self.price}, {self.date})'

    def dict(self) -> Mapping[str, Any]:
        return {
            col.name: getattr(self, col.name) for col in self.__table__.columns
        }

    def fulfill_category_prices(self) -> None:
        if self.type == ItemType.CATEGORY:
            self._count_category_offers_and_prices_sum()

    def _count_category_offers_and_prices_sum(self) -> tuple[int, int]:
        count = 0
        price_sum = 0
        for child in self.children:
            child: Item
            if child.type == ItemType.OFFER:
                count += 1
                price_sum += child.price
            elif child.type == ItemType.CATEGORY:
                cat_count, cat_sum = child._count_category_offers_and_prices_sum()
                count += cat_count
                price_sum += cat_sum

        if count > 0:
            self.price = price_sum // count
        return count, price_sum


@event.listens_for(Item, 'load')
def load_children(item: Item, _: orm.QueryContext) -> None:
    if item.type == ItemType.OFFER:
        orm.attributes.set_committed_value(item, 'children', None)
    elif item.type == ItemType.CATEGORY:
        orm.attributes.set_committed_value(item, 'children', item.children)
