from typing import Optional, List

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from meido.base_service import BaseService
from meido.dependence.database import Database
from meido.services.devices.models import DevicesDataBase as Devices

__all__ = ("DevicesRepository",)


class DevicesRepository(BaseService.Component):
    def __init__(self, database: Database):
        self.engine = database.engine

    async def get(
        self,
        account_id: int,
    ) -> Optional[Devices]:
        async with AsyncSession(self.engine) as session:
            statement = select(Devices).where(Devices.account_id == account_id)
            results = await session.exec(statement)
            return results.first()

    async def add(self, devices: Devices) -> None:
        async with AsyncSession(self.engine) as session:
            session.add(devices)
            await session.commit()

    async def update(self, devices: Devices) -> Devices:
        async with AsyncSession(self.engine) as session:
            session.add(devices)
            await session.commit()
            await session.refresh(devices)
            return devices

    async def delete(self, devices: Devices) -> None:
        async with AsyncSession(self.engine) as session:
            await session.delete(devices)
            await session.commit()

    async def get_all(self, is_valid: bool = None) -> List[Devices]:
        async with AsyncSession(self.engine) as session:
            statement = select(Devices)
            if is_valid is not None:
                statement = statement.where(Devices.is_valid == is_valid)
            results = await session.exec(statement)
            return results.all()
