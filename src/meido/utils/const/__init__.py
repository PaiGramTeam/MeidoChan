"""一些常量"""
from functools import WRAPPER_ASSIGNMENTS as _WRAPPER_ASSIGNMENTS
from typing import List

from meido.utils.const._path import *
from meido.utils.const._single import *

NOT_SET = object()
# noinspection PyTypeChecker
WRAPPER_ASSIGNMENTS: List[str] = list(_WRAPPER_ASSIGNMENTS) + [
    "block",
    "_catch_targets",
    "_handler_datas",
    "_conversation_handler_data",
    "_error_handler_data",
    "_job_data",
]

USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/90.0.4430.72 Safari/537.36"
)
REQUEST_HEADERS: dict = {"User-Agent": USER_AGENT}
