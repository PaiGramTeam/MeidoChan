from abc import ABC, abstractmethod
from typing import Optional, TypeVar, List, Any, Tuple, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from meido.services.players.models import PlayersDataBase as Player

T = TypeVar("T")


class MigrateDataException(Exception):
    """迁移数据异常"""

    def __init__(self, msg: str):
        self.msg = msg


class IMigrateData(ABC):
    @abstractmethod
    async def migrate_data_msg(self) -> str:
        """返回迁移数据的提示信息"""

    @abstractmethod
    async def migrate_data(self) -> bool:
        """迁移数据"""

    @staticmethod
    def get_sql_data_by_key(model: T, keys: Tuple[Any, ...]) -> tuple[Any, ...]:
        """通过 key 获取数据"""
        data = []
        for i in keys:
            data.append(getattr(model, i.key))
        return tuple(data)

    @staticmethod
    async def filter_sql_data(
        model: Type[T], service_method, old_user_id: int, new_user_id: int, keys: Tuple[Any, ...]
    ) -> Tuple[List[T], List[T]]:
        """过滤数据库数据"""
        data: List[model] = await service_method(old_user_id)
        if not data:
            return [], []
        new_data = await service_method(new_user_id)
        new_data_index = [IMigrateData.get_sql_data_by_key(p, keys) for p in new_data]
        need_migrate = []
        for d in data:
            if IMigrateData.get_sql_data_by_key(d, keys) not in new_data_index:
                need_migrate.append(d)
        return need_migrate, new_data


class MigrateData:
    async def get_migrate_data(
        self, old_user_id: int, new_user_id: int, old_players: List["Player"]
    ) -> Optional[IMigrateData]:
        """获取迁移数据"""
        if not (old_user_id and new_user_id and old_players):
            return None
        return None
