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
        CREATE OR REPLACE TRIGGER update_category_date_e
            AFTER INSERT OR UPDATE ON items
            FOR EACH ROW EXECUTE PROCEDURE update_category_date();
        ''')

        event.listen(
            Item.__table__, 'after_create', update_category_date_function,
        )
        event.listen(
            Item.__table__, 'after_create', update_category_date_trigger,
        )

        async with cls.engine() as conn:
            await conn.run_sync(Base.metadata.create_all)
