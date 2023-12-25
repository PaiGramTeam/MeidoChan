from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ConversationHandler

from meido.plugin._handler import conversation, handler
from meido.plugin.methods import PluginFuncMethods

__all__ = (
    "PluginFuncs",
    "ConversationFuncs",
)


class PluginFuncs(PluginFuncMethods):
    """插件方法"""


class ConversationFuncs:
    @conversation.fallback
    @handler.command(command="cancel", block=False)
    async def cancel(self, update: Update, _) -> int:
        await update.effective_message.reply_text("退出命令", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
