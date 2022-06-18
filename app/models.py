from sqlalchemy import Column, CheckConstraint, BigInteger, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Item(Base):
    __tablename__ = 'items'
    __table_args__ = (
        CheckConstraint('(children IS NULL) != (price IS NULL)'),
    )

    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    parent_id: str | None = Column(UUID)
    type = Column(String, CheckConstraint("type in ('OFFER', 'CATEGORY')"))
    price: int | None = Column(BigInteger)
    children: str | None = Column(UUID)

    def __repr__(self):
        return f'Item(type={self.type}, name={self.name}, price={self.price})'
