from aiohttp.web_app import Application
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine, AsyncConnection
from sqlalchemy.orm import sessionmaker

from .models import Base


class Database:
    _engine: AsyncEngine
    _session_maker: sessionmaker

    @classmethod
    async def connect(cls, app: Application):
        db_dsn = URL.create('postgresql+asyncpg', **app['config']['db'])
        cls._engine = create_async_engine(db_dsn, future=True)
        cls._session_maker = sessionmaker(
            cls._engine, expire_on_commit=False, class_=AsyncSession,
        )

        async with cls.connection() as conn:  # TODO move to migrations
            await conn.run_sync(Base.metadata.create_all)

    @classmethod
    async def disconnect(cls, _: Application):
        await cls._engine.dispose()

    @classmethod
    def connection(cls) -> AsyncConnection:
        return cls._engine.begin()

    @classmethod
    def session(cls) -> AsyncSession:
        return cls._session_maker()
