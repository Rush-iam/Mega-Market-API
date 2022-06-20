from sqlalchemy import Column, CheckConstraint, ForeignKey, BigInteger, String, TIMESTAMP, event, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship, attributes, QueryContext

Base = declarative_base()

# class Stats(Base):
#     id = Column(Integer, primary_key=True)
#     date = Column(TIMESTAMP(timezone=True), nullable=False)
#     item_id = Column(UUID(as_uuid=True), ForeignKey(Item.id, ondelete='CASCADE'))
#     price = Column(BigInteger)


class Item(Base):
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    date = Column(TIMESTAMP(timezone=True), nullable=False)
    parent_id: str | None = Column(
        UUID(as_uuid=True), ForeignKey(id, ondelete='CASCADE'), index=True,
    )
    type = Column(String, CheckConstraint("type in ('OFFER', 'CATEGORY')"))
    price: int | None = Column(BigInteger, CheckConstraint('price >= 0'))

    children = relationship(
        lambda: Item,
        cascade='save-update, merge, expunge, delete',
        passive_deletes=True,
    )

    __tablename__ = 'items'
    __table_args__ = (
        CheckConstraint(
            "type != 'CATEGORY' OR price IS NULL",
            name='category_price_is_null'
        ),
        CheckConstraint(
            "type != 'OFFER' OR price IS NOT NULL",
            name='offer_price_is_not_null'
        ),
    )

    def __repr__(self):
        return f'Item({self.type}, {self.name}, {self.price}, {self.date})'

    def dict(self):
        return {
            col.name: getattr(self, col.name) for col in self.__table__.columns
        }


@event.listens_for(Item, 'load')
def load_children(item: Item, _: QueryContext):
    if item.type == 'OFFER':
        attributes.set_committed_value(item, 'children', None)
    elif item.type == 'CATEGORY':
        attributes.set_committed_value(item, 'children', item.children)
