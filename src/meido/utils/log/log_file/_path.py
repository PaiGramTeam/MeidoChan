import datetime
import os

from meido.utils.log.log_file._datetime import FileDateFormatter

__all__ = ("generate_rename_path",)


def generate_rename_path(root: str, ext: str, creation_time: float) -> str:
    creation_datetime = datetime.datetime.fromtimestamp(creation_time)
    date = FileDateFormatter(creation_datetime)

    renamed_path = "{}.{}{}".format(root, date, ext)
    counter = 1

    while os.path.exists(renamed_path):
        counter += 1
        renamed_path = "{}.{}.{}{}".format(root, date, counter, ext)

    return renamed_path
