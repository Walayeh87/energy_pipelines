import logging
import sys
from logging import LogRecord

RESET = "\033[0m"

COLORS = {
    logging.DEBUG: "\033[36m",  # cyan
    logging.INFO: "\033[37m",  # white
    logging.WARNING: "\033[33m",  # yellow
    logging.ERROR: "\033[31m",  # red
    logging.CRITICAL: "\033[35;1m",  # bright magenta
}


class ColorFormatter(logging.Formatter):
    def format(self, record: LogRecord) -> str:
        message = super().format(record)
        color = COLORS.get(record.levelno, "")
        reset = RESET if color else ""
        return f"{color}{message}{reset}"


def setup_logging(level: int = logging.DEBUG) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter("%(levelname)s | %(filename)s | line: %(lineno)d | %(message)s"))

    logging.basicConfig(level=level, handlers=[handler], force=True)
