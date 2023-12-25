from typing import Optional

from meido.base_service import BaseService
from meido.services.devices.repositories import DevicesRepository
from meido.services.devices.models import DevicesDataBase as Devices


class DevicesService(BaseService):
    def __init__(self, devices_repository: DevicesRepository) -> None:
        self._repository: DevicesRepository = devices_repository

    async def update(self, devices: Devices):
        await self._repository.update(devices)

    async def add(self, devices: Devices):
        await self._repository.add(devices)

    async def get(
        self,
        account_id: int,
    ) -> Optional[Devices]:
        return await self._repository.get(account_id)

    async def delete(self, devices: Devices) -> None:
        return await self._repository.delete(devices)
