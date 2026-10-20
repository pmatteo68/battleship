"""Logging configuration for Battleship. Edit the three settings below."""
import logging
import os

_ENV_LEVEL = os.environ.get("GAME_LOG_LEVEL", "").upper()
_LEVEL_MAP = {
    "DEBUG":    logging.DEBUG,
    "INFO":     logging.INFO,
    "WARNING":  logging.WARNING,
    "ERROR":    logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

LOG_LEVEL   = _LEVEL_MAP.get(_ENV_LEVEL, logging.DEBUG)
LOG_FILE    = "battleship.log"
LOG_CONSOLE = True

_FMT = (
    "%(asctime)s.%(msecs)03d "
    "[%(threadName)s] "
    "%(levelname)s "
    "%(name)s:%(lineno)d - "
    "%(message)s"
)
_DATE = "%Y-%m-%d %H:%M:%S"


def setup() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(LOG_LEVEL)
    fmt = logging.Formatter(_FMT, datefmt=_DATE)
    if LOG_FILE:
        fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
        fh.setFormatter(fmt)
        root.addHandler(fh)
    if LOG_CONSOLE:
        import sys
        ch = logging.StreamHandler(sys.stderr)
        ch.setFormatter(fmt)
        root.addHandler(ch)
