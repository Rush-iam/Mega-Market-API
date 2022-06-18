from aiohttp.web_app import Application
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


class Database:
    def __init__(self, config: dict[str, str]):
        db_dsn = URL.create('postgresql+asyncpg', **config)
        engine = create_async_engine(db_dsn, future=True)
        self.session = sessionmaker(engine, class_=AsyncSession, future=True)

        # async with self.db.begin() as conn:
        #     await conn.run_sync(Base.metadata.create_all)

    async def disconnect(self, _: Application):
        self.session.close_all()
