from pathlib import Path
from typing import List, Literal, Optional, Union

from pydantic import BaseSettings

from meido.config import LogTracebackConfig, Settings
from meido.utils.const import PROJECT_ROOT

__all__ = ("LoggerConfig",)


class LoggerConfig(BaseSettings):
    name: str = "PaiGram-logger"
    """logger 名称"""
    level: Optional[Union[str, int]] = None
    """logger 的 level"""

    multiprocess: bool = True
    """是否启用多进程"""

    width: Optional[int] = None
    """输出时的宽度"""
    keywords: List[str] = []
    """高亮的关键字"""
    time_format: str = "[%Y-%m-%d %X]"
    """时间格式"""
    omit_repeated_times: bool = True
    """是否忽略重复的时间"""
    capture_warnings: bool = True
    """是否捕获 warning"""
    color_system: Literal["auto", "standard", "256", "truecolor", "windows"] = "auto"
    """颜色模式： 自动、标准、256色、真彩、Windows模式. *不建议修改*"""

    log_path: Union[str, Path] = "./logs"
    """log 所保存的路径，项目根目录的相对路径"""
    project_root: Union[str, Path] = PROJECT_ROOT
    """项目根目录"""

    traceback: LogTracebackConfig = LogTracebackConfig()
