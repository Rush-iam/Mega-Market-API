from collections.abc import Mapping
from enum import Enum
from typing import Any

from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger
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
        # TODO: uncomment after Alembic 1.9+ implement column checks detection
        # CheckConstraint(
        #     f"type in ('{ItemType.OFFER}', '{ItemType.CATEGORY}')",
        #     name='type_value_check'
        # )
    )
    price: int | None = Column(
        BigInteger,
        # TODO: uncomment after Alembic 1.9+ implement column checks detection
        # CheckConstraint(
        #     'price >= 0',
        #     name='price_value_check'
        # )
    )

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

        # TODO: move to column after Alembic 1.9+ implement detection there
        CheckConstraint(
            f"type in ('{ItemType.OFFER}', '{ItemType.CATEGORY}')",
            name='type_value_check'
        ),
        # TODO: move to column after Alembic 1.9+ implement detection there
        CheckConstraint(
            'price >= 0',
            name='price_value_check'
        )
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


def item_database_triggers():
    return {

        'get_item_type': PGFunction(
            schema='public',
            signature='get_item_type(item_id UUID)',
            definition=f'''
                RETURNS VARCHAR AS
                $$
                BEGIN
                    RETURN (
                        SELECT type
                            FROM {Item.__tablename__}
                            WHERE id = item_id
                    );
                END;
                $$ language 'plpgsql';
            '''
        ),

        'update_category_date': PGFunction(
            schema='public',
            signature='update_category_date()',
            definition=f'''
                RETURNS TRIGGER AS
                $$
                BEGIN
                    UPDATE {Item.__tablename__}
                        SET date = NEW.date
                        WHERE id = NEW.parent_id;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            '''),
        'update_category_date_trigger': PGTrigger(
            schema='public',
            signature='update_category_date',
            on_entity=f'public.{Item.__tablename__}',
            definition=f'''
                AFTER INSERT OR UPDATE ON {Item.__tablename__} FOR EACH ROW
                WHEN (NEW.parent_id IS NOT NULL)
                EXECUTE PROCEDURE update_category_date();
            '''
        ),

        'exception_type_modified': PGFunction(
            schema='public',
            signature='exception_type_modified()',
            definition='''
                RETURNS TRIGGER AS
                $$
                BEGIN
                    RAISE EXCEPTION
                        'Modification of column - type - is forbidden'
                        USING ERRCODE = 'check_violation';
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            '''
        ),
        'check_type_modified_trigger': PGTrigger(
            schema='public',
            signature='check_type_modified',
            on_entity=f'public.{Item.__tablename__}',
            definition=f'''
                BEFORE UPDATE ON {Item.__tablename__} FOR EACH ROW
                WHEN (NEW.type IS DISTINCT FROM OLD.type)
                EXECUTE PROCEDURE exception_type_modified();
            '''
        ),

        'check_parent_is_category': PGFunction(
            schema='public',
            signature='check_parent_is_category()',
            definition=f'''
                RETURNS TRIGGER AS
                $$
                BEGIN
                if get_item_type(NEW.parent_id) != '{ItemType.CATEGORY}' THEN
                    RAISE EXCEPTION
                        'Parent must be - {ItemType.CATEGORY}'
                        USING ERRCODE = 'check_violation';
                END IF;
                RETURN NEW;
                END;
                $$ language 'plpgsql';
            ''',
        ),
        'check_parent_is_category_trigger': PGTrigger(
            schema='public',
            signature='check_parent_is_category',
            on_entity=f'public.{Item.__tablename__}',
            definition=f'''
                AFTER INSERT OR UPDATE ON {Item.__tablename__} FOR EACH ROW
                EXECUTE PROCEDURE check_parent_is_category();
            '''
        ),

    }.values()
