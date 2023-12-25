import ujson as jsonlib
from pydantic import BaseSettings

__all__ = ("Settings",)


class Settings(BaseSettings):
    def __new__(cls, *args, **kwargs):
        cls.update_forward_refs()
        return super(Settings, cls).__new__(cls)  # pylint: disable=E1120

    class Config(BaseSettings.Config):
        case_sensitive = False
        json_loads = jsonlib.loads
        json_dumps = jsonlib.dumps
