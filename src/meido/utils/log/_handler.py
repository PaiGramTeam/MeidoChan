import logging
import os
import site
import sys
from datetime import datetime
from functools import lru_cache
from logging import LogRecord
from pathlib import Path
from typing import IO, Literal, TYPE_CHECKING

from rich.console import Console
from rich.containers import Renderables
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from meido.config import LogTracebackConfig
from meido.utils.const import PKG_ROOT, PROJECT_ROOT
from meido.utils.log._style import DEFAULT_STYLE
from meido.utils.log._traceback import Traceback

if TYPE_CHECKING:
    from rich.console import ConsoleRenderable, RenderableType

__all__ = ("Handler",)


@lru_cache()
def resolve_sit_path(path: Path | str) -> str:
    result = None
    for s in site.getsitepackages():
        try:
            result = Path(path).relative_to(Path(s))
            break
        except (ValueError, TypeError):
            continue
    if result is None:
        result = "<SITE>"
    else:
        result = str(result.with_suffix("")).replace(os.sep, ".")
    return result


@lru_cache()
def in_pkg_root(path: Path | str) -> bool:
    try:
        Path(path).relative_to(PKG_ROOT)
        return True
    except ValueError:
        return False


@lru_cache()
def resolve_log_path(path: str | Path, root: Path = Path(os.curdir).resolve()) -> str:
    if path != "<input>":
        if in_pkg_root(path):
            result = str(Path(path).relative_to(PKG_ROOT).with_suffix("")).replace(os.sep, ".")
        else:
            try:
                result = str(Path(path).relative_to(root).with_suffix("")).replace(os.sep, ".")
            except ValueError:
                result = resolve_sit_path(path)
    else:
        result = "<INPUT>"  # stdin
    return result.replace("lib.site-packages.", "")


class Handler(logging.Handler):  # skipcq: PY-A6006
    @property
    def console(self) -> Console:
        return self._console

    def __init__(
        self,
        level: int | str = 0,
        *,
        file: IO[str] = sys.stdout,
        width: int | None = None,
        color_system: Literal["auto", "standard", "256", "truecolor", "windows"] = "auto",
        omit_repeated_times: bool = True,
        show_path: bool = True,
        enable_link_path: bool = True,
        markup: bool = False,
        keywords: list[str] | None = None,
        time_format: str | None = None,
        rich_tracebacks: bool = True,
        traceback_configs: LogTracebackConfig | None = None,
        project_root: Path | None = None,
    ) -> None:
        super().__init__(level)
        self._console = Console(
            width=width,
            color_system=color_system,
            theme=Theme(DEFAULT_STYLE),
            file=file,
        )
        self.omit_repeated_times = omit_repeated_times
        self.show_path = show_path
        self.enable_link_path = enable_link_path
        self.markup = markup
        self.keywords = keywords
        self.time_format = time_format or "%X"
        self.rich_tracebacks = rich_tracebacks
        self.traceback_configs = traceback_configs or LogTracebackConfig()
        self.project_root = project_root or PROJECT_ROOT

        self._last_time = None

    def _get_message_renderable(self, record: LogRecord, message: str) -> Text:
        markup: bool = getattr(record, "markup", self.markup)
        keywords: list[str] = list(set(getattr(record, "keywords", []) + (self.keywords or [])))

        message_text = Text.from_markup(message) if markup else Text(message)

        if keywords:
            message_text.highlight_words(keywords, "logging.keyword")
        return message_text

    def _get_log_time(self, record: LogRecord) -> str | Text:
        log_time = datetime.fromtimestamp(record.created)
        time_formatter = None if self.formatter is None else self.formatter.datefmt
        return time_formatter(log_time) if callable(time_formatter) else Text(log_time.strftime(self.time_format))

    def render(self, record: LogRecord, message: str) -> "ConsoleRenderable":
        depth: int = getattr(record, "depth", self.traceback_configs.locals.max_depth)
        suppress: list[str] | None = getattr(record, "suppress", None)

        traceback = None
        if self.rich_tracebacks and record.exc_info and record.exc_info != (None, None, None):
            exc_type, exc_value, exc_traceback = record.exc_info
            assert exc_type is not None
            assert exc_value is not None
            traceback = Traceback.from_exception(
                exc_type,
                exc_value,
                exc_traceback,
                width=None,
                word_wrap=self.traceback_configs.word_wrap,
                show_locals=self.traceback_configs.locals.enable,
                locals_max_length=self.traceback_configs.locals.max_length,
                locals_max_string=self.traceback_configs.locals.max_string,
                locals_max_depth=depth,
                suppress=suppress if suppress is not None else self.traceback_configs.suppress,
            )
            message = record.getMessage()
            if self.formatter:
                record.message = record.getMessage()
                formatter = self.formatter
                if hasattr(formatter, "usesTime") and formatter.usesTime():
                    record.asctime = formatter.formatTime(record, formatter.datefmt)
                message = formatter.formatMessage(record)

        message_renderable = self._get_message_renderable(record, message)

        path = resolve_log_path(record.pathname, PROJECT_ROOT)

        level_name = record.levelname
        level_text = Text.styled(level_name.ljust(8), f"logging.level.{level_name.lower()}")

        renderables = [i for i in [message_renderable, traceback] if i is not None and i]

        output = Table.grid(padding=(0, 1), expand=True)
        output.add_column(style="log.time")
        output.add_column(style="log.level", width=8)
        output.add_column(ratio=1, style="log.message", overflow="fold")
        output.add_column(style="log.path")
        output.add_column(style="log.line_no", width=4)

        row: list["RenderableType"] = []

        log_time_display = self._get_log_time(record)
        if log_time_display == self._last_time and self.omit_repeated_times:
            row.append(Text(" " * len(log_time_display)))
        else:
            row.append(log_time_display)
            self._last_time = log_time_display

        row.append(level_text)
        row.append(Renderables(renderables))

        path_text = Text()
        path_text.append(path, style=f"link file://{record.pathname}")
        row.append(path_text)

        line_no_text = Text()
        line_no_text.append(
            str(record.lineno),
            style=f"link file://{record.pathname}#{record.lineno}",
        )
        row.append(line_no_text)
        output.add_row(*row)
        return output

    def emit(self, record: LogRecord) -> None:
        message = self.format(record)

        log_renderable = self.render(record=record, message=message)

        # noinspection PyBroadException
        try:
            self.console.print(log_renderable)
        except Exception:  # skipcq: PYL-W0703
            self.handleError(record)
        return None

    # noinspection PyProtectedMember
    def close(self) -> None:
        """Close handler"""
        if not self._console._file.closed:  # skipcq: PYL-W0212
            self._console._file.close()  # skipcq: PYL-W0212
