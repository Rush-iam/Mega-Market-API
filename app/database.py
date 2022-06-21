from aiohttp.web_app import Application
from sqlalchemy import event, DDL
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine, AsyncConnection
from sqlalchemy.orm import sessionmaker

from .models import Base, Item


class Database:
    _engine: AsyncEngine
    _session_maker: sessionmaker

    @classmethod
    async def connect(cls, app: Application):
        db_dsn = URL.create('postgresql+asyncpg', **app['config']['db'])
        cls._engine = create_async_engine(db_dsn, future=True, echo=True)
        cls._session_maker = sessionmaker(
            cls._engine, expire_on_commit=False, class_=AsyncSession,
        )
        await cls._init()  # TODO: move init to migrations

    @classmethod
    async def disconnect(cls, _: Application):
        await cls._engine.dispose()

    @classmethod
    def engine(cls) -> AsyncConnection:
        return cls._engine.begin()

    @classmethod
    def session(cls) -> AsyncSession:
        return cls._session_maker.begin()

    # TODO: move init to migrations
    @classmethod
    async def _init(cls):
        get_item_type_function = DDL('''
        CREATE OR REPLACE FUNCTION get_item_type(item_id UUID)
            RETURNS VARCHAR AS
        $$
        BEGIN
            RETURN (SELECT type FROM items WHERE id = item_id);
        END;
        $$ language 'plpgsql';
        ''')

        update_category_date_function = DDL('''
        CREATE OR REPLACE FUNCTION update_category_date()
            RETURNS TRIGGER AS
        $$
        BEGIN
            UPDATE items SET date = NEW.date WHERE id = NEW.parent_id;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        ''')

        update_category_date_trigger = DDL('''
        CREATE OR REPLACE TRIGGER update_category_date
            AFTER INSERT OR UPDATE ON items
            FOR EACH ROW EXECUTE PROCEDURE update_category_date();
        ''')

        check_type_not_modified = DDL('''
        CREATE OR REPLACE FUNCTION check_type_not_modified()
            RETURNS TRIGGER AS
        $$
        BEGIN
            if (NEW.type IS NOT NULL) AND (NEW.type != OLD.type) THEN
                RAISE EXCEPTION
                    'Modification of column - type - is forbidden'
                    USING ERRCODE = 'check_violation';
            END IF;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        ''')

        check_type_not_modified_trigger = DDL('''
        CREATE OR REPLACE TRIGGER check_type_not_modified
            BEFORE UPDATE ON items
            FOR EACH ROW EXECUTE PROCEDURE check_type_not_modified();
        ''')

        check_parent_is_category = DDL('''
        CREATE OR REPLACE FUNCTION check_parent_is_category()
            RETURNS TRIGGER AS
        $$
        BEGIN
            if get_item_type(NEW.parent_id) != 'CATEGORY' THEN
                RAISE EXCEPTION
                    'Parent must be - CATEGORY'
                    USING ERRCODE = 'check_violation';
            END IF;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        ''')

        check_parent_is_category_trigger = DDL('''
        CREATE OR REPLACE TRIGGER check_parent_is_category
            AFTER INSERT OR UPDATE ON items
            FOR EACH ROW EXECUTE PROCEDURE check_parent_is_category();
        ''')

        for table_event, sql_statement in (
            ('before_create', get_item_type_function),
            ('after_create', update_category_date_function),
            ('after_create', update_category_date_trigger),
            ('after_create', check_type_not_modified),
            ('after_create', check_type_not_modified_trigger),
            ('after_create', check_parent_is_category),
            ('after_create', check_parent_is_category_trigger),
        ):
            event.listen(Item.__table__, table_event, sql_statement)

        async with cls.engine() as conn:
            await conn.run_sync(Base.metadata.create_all)
