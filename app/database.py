import os

from aiohttp.web_app import Application
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncEngine, AsyncConnection, AsyncSession
)
from sqlalchemy.orm import sessionmaker


class Database:
    _engine: AsyncEngine
    _session_maker: sessionmaker

    @classmethod
    async def connect(cls, app: Application) -> None:
        cls._engine = create_async_engine(
            url=URL.create('postgresql+asyncpg', **app['config']['db']),
            future=True,  # TODO: remove after upgrading to SQLAlchemy 2.0
            echo=os.getenv('DEBUG') is not None,
        )
        cls._session_maker = sessionmaker(
            cls._engine,
            expire_on_commit=False,
            class_=AsyncSession,
            future=True,  # TODO: remove after upgrading to SQLAlchemy 2.0
        )

    @classmethod
    async def disconnect(cls, _: Application) -> None:
        await cls._engine.dispose()

    @classmethod
    def engine(cls) -> AsyncConnection:
        return cls._engine.begin()

    @classmethod
    def session(cls) -> AsyncSession:
        return cls._session_maker.begin()
