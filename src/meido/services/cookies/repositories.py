from typing import Optional, List, Tuple

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from meido.base_service import BaseService
from meido.basemodel import RegionEnum
from meido.dependence.database import Database
from meido.services.cookies.models import CookiesDataBase as Cookies, CookiesStatusEnum
from meido.services.devices.models import DevicesDataBase as Devices

__all__ = ("CookiesRepository",)


class CookiesRepository(BaseService.Component):
    def __init__(self, database: Database):
        self.engine = database.engine

    async def get(
        self,
        user_id: int,
        account_id: Optional[int] = None,
        region: Optional[RegionEnum] = None,
    ) -> Optional[Cookies]:
        async with AsyncSession(self.engine) as session:
            statement = select(Cookies).where(Cookies.user_id == user_id)
            if account_id is not None:
                statement = statement.where(Cookies.account_id == account_id)
            if region is not None:
                statement = statement.where(Cookies.region == region)
            results = await session.exec(statement)
            return results.first()

    async def add(self, cookies: Cookies) -> None:
        async with AsyncSession(self.engine) as session:
            session.add(cookies)
            await session.commit()

    async def update(self, cookies: Cookies) -> Cookies:
        async with AsyncSession(self.engine) as session:
            session.add(cookies)
            await session.commit()
            await session.refresh(cookies)
            return cookies

    async def delete(self, cookies: Cookies) -> None:
        async with AsyncSession(self.engine) as session:
            await session.delete(cookies)
            await session.commit()

    async def get_all(
        self,
        user_id: Optional[int] = None,
        account_id: Optional[int] = None,
        region: Optional[RegionEnum] = None,
        status: Optional[CookiesStatusEnum] = None,
    ) -> List[Cookies]:
        async with AsyncSession(self.engine) as session:
            statement = select(Cookies)
            if user_id is not None:
                statement = statement.where(Cookies.user_id == user_id)
            if account_id is not None:
                statement = statement.where(Cookies.account_id == account_id)
            if region is not None:
                statement = statement.where(Cookies.region == region)
            if status is not None:
                statement = statement.where(Cookies.status == status)
            results = await session.exec(statement)
            return results.all()

    async def get_by_devices(self, is_valid: bool = None) -> List[Tuple[Cookies, Devices]]:
        async with AsyncSession(self.engine) as session:
            statement = select(Cookies, Devices).where(Cookies.account_id == Devices.account_id)
            if is_valid is not None:
                statement = statement.where(Devices.is_valid == is_valid)
            results = await session.exec(statement)
            return results.all()
