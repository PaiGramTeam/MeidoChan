from typing import Optional, Union, TYPE_CHECKING

from telegram import Chat, Message
from telegram.error import Forbidden, NetworkError
from telegram.ext import CallbackContext, Job

from meido.utils.log import logger

if TYPE_CHECKING:
    from . import PluginFuncMethods


class DeleteMessage:
    async def _delete_message(self: "PluginFuncMethods", context: "CallbackContext") -> None:
        job = context.job
        message_id = job.data
        chat_info = f"chat_id[{job.chat_id}]"

        try:
            chat = await self.get_chat(job.chat_id)
            full_name = chat.full_name
            if full_name:
                chat_info = f"{full_name}[{chat.id}]"
            else:
                chat_info = f"{chat.title}[{chat.id}]"
        except (NetworkError, Forbidden) as exc:
            logger.warning("获取 chat info 失败 %s", exc.message)
        except Exception as exc:
            logger.warning("获取 chat info 消息失败 %s", str(exc))

        logger.debug("删除消息 %s message_id[%s]", chat_info, message_id)

        try:
            # noinspection PyTypeChecker
            await context.bot.delete_message(chat_id=job.chat_id, message_id=message_id)
        except NetworkError as exc:
            logger.warning("删除消息 %s message_id[%s] 失败 %s", chat_info, message_id, exc.message)
        except Forbidden as exc:
            logger.warning("删除消息 %s message_id[%s] 失败 %s", chat_info, message_id, exc.message)
        except Exception as exc:
            logger.error("删除消息 %s message_id[%s] 失败 %s", chat_info, message_id, exc_info=exc)

    def add_delete_message_job(
        self: "PluginFuncMethods",
        message: Optional[Union[int, Message]] = None,
        *,
        delay: int = 60,
        name: Optional[str] = None,
        chat: Optional[Union[int, Chat]] = None,
        context: Optional[CallbackContext] = None,
    ) -> Job:
        """延迟删除消息"""

        if isinstance(message, Message):
            if chat is None:
                chat = message.chat_id
            message = message.id

        chat = chat.id if isinstance(chat, Chat) else chat

        job_queue = self.application.job_queue or context.job_queue

        if job_queue is None or chat is None:
            raise RuntimeError

        return job_queue.run_once(
            callback=self._delete_message,
            when=delay,
            data=message,
            name=f"{chat}|{message}|{name}|delete_message" if name else f"{chat}|{message}|delete_message",
            chat_id=chat,
            job_kwargs={
                "replace_existing": True,
                "id": f"{chat}|{message}|delete_message",
            },
        )
