import os

__all__ = ("get_ctime", "set_ctime")


get_ctime = set_ctime = None

if os.name == "nt":
    import win32_setctime

    def get_ctime(filepath):
        return os.stat(filepath).st_ctime

    def set_ctime(filepath, timestamp):
        if not win32_setctime.SUPPORTED:
            return

        try:
            win32_setctime.setctime(filepath, timestamp)
        except (OSError, ValueError):
            pass


if hasattr(os.stat_result, "st_birthtime"):

    def get_ctime(filepath):
        return os.stat(filepath).st_birthtime

    def set_ctime(*_):
        """Do Nothing."""


# noinspection SpellCheckingInspection
if hasattr(os, "getxattr") and hasattr(os, "setxattr"):

    def get_ctime(filepath):
        try:
            return float(os.getxattr(filepath, b"user.meido_chan_crtime"))
        except OSError:
            return os.stat(filepath).st_mtime

    def set_ctime(filepath, timestamp):
        try:
            os.setxattr(filepath, b"user.meido_chan_crtime", str(timestamp).encode("ascii"))
        except OSError:
            pass


if get_ctime is None and set_ctime is None:

    def get_ctime(filepath):
        return os.stat(filepath).st_mtime

    def set_ctime(*_):
        """Do Nothing."""
