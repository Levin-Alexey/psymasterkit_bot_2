import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


load_dotenv()

raw_database_url = os.getenv("DATABASE_URL", "").strip()
# Protect against accidental trailing character in .env (for example: ">")
DATABASE_URL = (
    raw_database_url[:-1]
    if raw_database_url.endswith(">")
    else raw_database_url
)

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is empty in .env")

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_models() -> None:
    from models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
