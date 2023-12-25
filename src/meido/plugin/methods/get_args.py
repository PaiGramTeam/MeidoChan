from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from telegram.ext import CallbackContext


class GetArgs:
    @staticmethod
    def get_args(context: "CallbackContext") -> List[str]:
        args = context.args
        match = context.match

        if args is None:
            if match is not None and (command := match.groups()[0]):
                temp = []
                command_parts = command.split(" ")
                for command_part in command_parts:
                    if command_part:
                        temp.append(command_part)
                return temp
            return []
        if len(args) >= 1:
            return args
        return []
