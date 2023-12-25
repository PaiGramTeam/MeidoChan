from typing import Optional, Union

import fakeredis.aioredis
from meido.utils.aioredis import aioredis, RedisTimeoutError, RedisConnectionError
from typing_extensions import Self

from meido.base_service import BaseService
from meido.config import ApplicationConfig
from meido.utils.log import logger

__all__ = ("Redis", )


class Redis(BaseService.Dependence):
    @classmethod
    def from_config(cls, config: ApplicationConfig) -> Self:
        return cls(**config.redis.dict())

    def __init__(
        self, host: str = "127.0.0.1", port: int = 6379, database: Union[str, int] = 0, password: Optional[str] = None
    ):
        self.client = aioredis.Redis(host=host, port=port, db=database, password=password)
        self.ttl = 600

    async def ping(self):
        # noinspection PyUnresolvedReferences
        if await self.client.ping():
            logger.info("连接 [red]Redis[/] 成功", extra={"markup": True})
        else:
            logger.info("连接 [red]Redis[/] 失败", extra={"markup": True})
            raise RuntimeError("连接 Redis 失败")

    async def start_fake_redis(self):
        self.client = fakeredis.aioredis.FakeRedis()
        await self.ping()

    async def initialize(self):
        logger.info("正在尝试建立与 [red]Redis[/] 连接", extra={"markup": True})
        try:
            await self.ping()
        except (RedisTimeoutError, RedisConnectionError) as exc:
            if isinstance(exc, RedisTimeoutError):
                logger.warning("连接 [red]Redis[/] 超时，使用 [red]fakeredis[/] 模拟", extra={"markup": True})
            if isinstance(exc, RedisConnectionError):
                logger.warning("连接 [red]Redis[/] 失败，使用 [red]fakeredis[/] 模拟", extra={"markup": True})
            await self.start_fake_redis()

    async def shutdown(self):
        await self.client.close()
