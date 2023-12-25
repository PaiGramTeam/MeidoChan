from typing import List, Optional

from meido.base_service import BaseService
from meido.basemodel import RegionEnum
from meido.services.cookies.cache import PublicCookiesCache
from meido.services.cookies.error import TooManyRequestPublicCookies
from meido.services.cookies.models import CookiesDataBase as Cookies, CookiesStatusEnum
from meido.services.cookies.repositories import CookiesRepository
from meido.services.devices.repositories import DevicesRepository
from utils.log import logger

__all__ = ("CookiesService", "PublicCookiesService", "NeedContinue")


class NeedContinue(Exception):
    pass


class CookiesService(BaseService):
    def __init__(self, cookies_repository: CookiesRepository) -> None:
        self._repository: CookiesRepository = cookies_repository

    async def update(self, cookies: Cookies):
        await self._repository.update(cookies)

    async def add(self, cookies: Cookies):
        await self._repository.add(cookies)

    async def get(
        self,
        user_id: int,
        account_id: Optional[int] = None,
        region: Optional[RegionEnum] = None,
    ) -> Optional[Cookies]:
        return await self._repository.get(user_id, account_id, region)

    async def delete(self, cookies: Cookies) -> None:
        return await self._repository.delete(cookies)

    async def get_all(
        self,
        user_id: Optional[int] = None,
        account_id: Optional[int] = None,
        region: Optional[RegionEnum] = None,
        status: Optional[CookiesStatusEnum] = None,
    ) -> List[Cookies]:
        return await self._repository.get_all(user_id, account_id, region, status)


class PublicCookiesService:
    def __init__(
        self,
        cookies_repository: CookiesRepository,
        public_cookies_cache: PublicCookiesCache,
        devices_repository: DevicesRepository,
    ):
        self._cache = public_cookies_cache
        self._repository: CookiesRepository = cookies_repository
        self.devices_repository = devices_repository
        self.count: int = 0
        self.user_times_limiter = 3 * 3

    async def initialize(self) -> None:
        logger.info("正在初始化公共Cookies池")
        await self.refresh()
        logger.success("刷新公共Cookies池成功")

    async def refresh(self):
        """刷新公共Cookies 定时任务
        :return:
        """
        user_list: List[int] = []
        data_list = await self._repository.get_by_devices(is_valid=True)
        for cookies, devices in data_list:
            user_list.append(cookies.user_id)
        if len(user_list) > 0:
            add, count = await self._cache.add_public_cookies(user_list, RegionEnum.HYPERION)
            logger.info("国服公共Cookies池已经添加[%s]个 当前成员数为[%s]", add, count)
        user_list.clear()
        cookies_list = await self._repository.get_all(
            region=RegionEnum.HOYOLAB, status=CookiesStatusEnum.STATUS_SUCCESS
        )
        for cookies in cookies_list:
            user_list.append(cookies.user_id)
        if len(user_list) > 0:
            add, count = await self._cache.add_public_cookies(user_list, RegionEnum.HOYOLAB)
            logger.info("国际服公共Cookies池已经添加[%s]个 当前成员数为[%s]", add, count)

    async def check_public_cookie(self, region: RegionEnum, cookies: Cookies, public_id: int):
        pass

    async def get_cookies(self, user_id: int, region: RegionEnum = RegionEnum.NULL):
        """获取公共Cookies
        :param user_id: 用户ID
        :param region: 注册的服务器
        :return:
        """
        user_times = await self._cache.incr_by_user_times(user_id)
        if int(user_times) > self.user_times_limiter:
            logger.warning("用户 %s 使用公共Cookies次数已经到达上限", user_id)
            raise TooManyRequestPublicCookies(user_id)
        while True:
            public_id, count = await self._cache.get_public_cookies(region)
            cookies = await self._repository.get(public_id, region=region)
            if cookies is None:
                await self._cache.delete_public_cookies(public_id, region)
                continue
            try:
                await self.check_public_cookie(region, cookies, public_id)
                logger.info("用户 user_id[%s] 请求用户 user_id[%s] 的公共Cookies 该Cookies使用次数为%s次 ", user_id, public_id, count)
                return cookies
            except NeedContinue:
                continue

    async def undo(self, user_id: int, cookies: Optional[Cookies] = None, status: Optional[CookiesStatusEnum] = None):
        await self._cache.incr_by_user_times(user_id, -1)
        if cookies is not None and status is not None:
            cookies.status = status
            await self._repository.update(cookies)
            await self._cache.delete_public_cookies(cookies.user_id, cookies.region)
            logger.info("用户 user_id[%s] 反馈用户 user_id[%s] 的Cookies状态为 %s", user_id, cookies.user_id, status.name)
        else:
            logger.info("用户 user_id[%s] 撤销一次公共Cookies计数", user_id)

    async def set_device_valid(self, account_id: int, is_valid: bool) -> None:
        device = await self.devices_repository.get(account_id)
        if device:
            device.is_valid = is_valid
            await self.devices_repository.update(device)
