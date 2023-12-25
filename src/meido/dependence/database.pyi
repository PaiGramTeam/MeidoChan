from typing import AsyncContextManager, Self, ClassVar, Optional

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import async_sessionmaker, async_scoped_session, AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from gram_core.base_service import BaseService
from gram_core.config import ApplicationConfig

class Database(BaseService.Dependence):
    _url: URL
    _engine: AsyncEngine
    _session: async_sessionmaker
    _session_factory: async_scoped_session
    _session_class: ClassVar[AsyncSession]

    def __init__(
        self,
        driver_name: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ): ...
    @classmethod
    def from_config(cls, config: ApplicationConfig) -> Self: ...
    @property
    def engine(self) -> AsyncEngine: ...
    async def session(self) -> AsyncContextManager[AsyncSession]:
        yield self._session_class
