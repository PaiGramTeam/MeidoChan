from typing import Union, Optional, TYPE_CHECKING

from telegram import Chat

from meido.dependence.redis import Redis

if TYPE_CHECKING:
    from . import PluginFuncMethods

try:
    import ujson as jsonlib
except ImportError:
    import json as jsonlib


class GetChat:
    async def get_chat(
        self: "PluginFuncMethods",
        chat_id: Union[str, int],
        redis_db: Optional[Redis] = None,
        expire: int = 86400,
    ) -> Chat:
        application = self.application
        redis_db: Redis = redis_db or self.application.managers.dependency_map.get(Redis, None)

        if not redis_db:
            return await application.bot.get_chat(chat_id)

        qname = f"bot:chat:{chat_id}"

        data = await redis_db.client.get(qname)
        if data:
            json_data = jsonlib.loads(data)
            return Chat.de_json(json_data, application.telegram.bot)

        chat_info = await application.telegram.bot.get_chat(chat_id)
        await redis_db.client.set(qname, chat_info.to_json(), ex=expire)
        return chat_info
