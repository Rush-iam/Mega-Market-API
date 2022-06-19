from sqlalchemy import Column, CheckConstraint, BigInteger, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Item(Base):  # TODO: switch to Table()?
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    date = Column(TIMESTAMP(timezone=True), nullable=False)
    parent_id: str | None = Column(UUID(as_uuid=True))
    type = Column(String, CheckConstraint("type in ('OFFER', 'CATEGORY')"))
    price: int | None = Column(BigInteger, CheckConstraint('price >= 0'))
    children: str | None = Column(UUID(as_uuid=True))

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
        CheckConstraint(
            "type != 'OFFER' OR children IS NULL",
            name='offer_children_is_null'
        ),
    )

    def __repr__(self):
        return f'Item(type={self.type}, name={self.name}, price={self.price}, date={self.date})'

    def dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}
