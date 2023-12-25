from contextlib import asynccontextmanager
from contextlib import asynccontextmanager
from typing import Optional, Self

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from meido.base_service import BaseService
from meido.config import ApplicationConfig

__all__ = ("Database",)


class Database(BaseService.Dependence):
    @classmethod
    def from_config(cls, config: ApplicationConfig) -> Self:
        return cls(**config.database.dict())

    def __init__(
        self,
        driver_name: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        self._url = URL.create(
            driver_name,
            username=username,
            password=password,
            host=host,
            port=port,
            database=database,
        )
        self._engine = create_async_engine(self._url)
        self._session = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
        )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @asynccontextmanager
    async def session(self):
        yield self._session()
