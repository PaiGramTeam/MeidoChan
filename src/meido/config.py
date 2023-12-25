from enum import Enum
from pathlib import Path
from typing import List, Optional, Set

import dotenv
from pydantic import AnyUrl, Field, BaseSettings

from meido.utils.const import PROJECT_ROOT

try:
    import ujson as jsonlib
except ImportError:
    import json as jsonlib

__all__ = ("ApplicationConfig", "config", "JoinGroups")

dotenv.load_dotenv(dotenv_path=dotenv.find_dotenv(usecwd=True))


class Settings(BaseSettings):
    def __new__(cls, *args, **kwargs):
        cls.update_forward_refs()
        return super(Settings, cls).__new__(cls)  # pylint: disable=E1120

    class Config(BaseSettings.Config):
        case_sensitive = False
        json_loads = jsonlib.loads
        json_dumps = jsonlib.dumps


class JoinGroups(str, Enum):
    NO_ALLOW = "NO_ALLOW"
    ALLOW_AUTH_USER = "ALLOW_AUTH_USER"
    ALLOW_USER = "ALLOW_USER"
    ALLOW_ALL = "ALLOW_ALL"


class DatabaseConfig(Settings):
    driver_name: str = "mysql+asyncmy"
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None

    class Config(Settings.Config):
        env_prefix = "db_"


class RedisConfig(Settings):
    host: str = "127.0.0.1"
    port: int = 6379
    database: int = Field(default=0, env="redis_db")
    password: Optional[str] = None

    class Config(Settings.Config):
        env_prefix = "redis_"


class LogTracebackConfig(Settings):
    class Config(Settings.Config):
        env_prefix = "logger_traceback_"

    class LogTraceLocalsConfig(Settings):
        enable: bool = True
        max_depth: int | None = None
        max_length: int = 10
        max_string: int = 80

        class Config(Settings.Config):
            env_prefix = "logger_traceback_locals_"

    max_frames: int = 20
    word_wrap: bool = False
    suppress: list[str] = []
    locals: LogTraceLocalsConfig = LogTraceLocalsConfig()


class LoggerConfig(Settings):
    name: str = "PaiGram"
    width: Optional[int] = None
    time_format: str = "[%Y-%m-%d %X]"
    capture_warnings: bool = True
    path: Path = PROJECT_ROOT / "logs"
    keywords: List[str] = ["BOT"]
    filtered_names: List[str] = ["uvicorn"]
    traceback: LogTracebackConfig = LogTracebackConfig()

    class Config(Settings.Config):
        env_prefix = "logger_"


class MTProtoConfig(Settings):
    api_id: Optional[int] = None
    api_hash: Optional[str] = None


class WebServerConfig(Settings):
    enable: bool = False
    """是否启用WebServer"""

    url: AnyUrl = "http://localhost:8080"
    host: str = "localhost"
    port: int = 8080

    class Config(Settings.Config):
        env_prefix = "web_"


class ErrorConfig(Settings):
    pb_url: str = ""
    pb_sunset: int = 43200
    pb_max_lines: int = 1000
    sentry_dsn: str = ""
    notification_chat_id: Optional[str] = None

    class Config(Settings.Config):
        env_prefix = "error_"


class ReloadConfig(Settings):
    delay: float = 0.25
    dirs: List[str] = []
    include: List[str] = []
    exclude: List[str] = []

    class Config(Settings.Config):
        env_prefix = "reload_"


class ApplicationConfig(Settings):
    debug: bool = False
    """debug 开关"""
    retry: int = 5
    """重试次数"""
    auto_reload: bool = False
    """自动重载"""

    proxy_url: Optional[AnyUrl] = None
    """代理链接"""

    bot_token: str = ""
    """BOT的token"""
    bot_base_url: str = "https://api.telegram.org/bot"
    """Telegram API URL"""
    bot_base_file_url: str = "https://api.telegram.org/file/bot"
    """Telegram API File URL"""

    owner: Optional[int] = None

    timeout: int = 10
    connection_pool_size: int = 256
    read_timeout: Optional[float] = None
    write_timeout: Optional[float] = None
    connect_timeout: Optional[float] = None
    pool_timeout: Optional[float] = None
    update_read_timeout: Optional[float] = None
    update_write_timeout: Optional[float] = None
    update_connect_timeout: Optional[float] = None
    update_pool_timeout: Optional[float] = None

    genshin_ttl: Optional[int] = None

    enka_network_api_agent: str = ""
    pass_challenge_api: str = ""
    pass_challenge_app_key: str = ""
    pass_challenge_user_web: str = ""

    reload: ReloadConfig = ReloadConfig()
    database: DatabaseConfig = DatabaseConfig()
    logger: LoggerConfig = LoggerConfig()
    webserver: WebServerConfig = WebServerConfig()
    redis: RedisConfig = RedisConfig()
    mtproto: MTProtoConfig = MTProtoConfig()
    error: ErrorConfig = ErrorConfig()


ApplicationConfig.update_forward_refs()
config = ApplicationConfig()
