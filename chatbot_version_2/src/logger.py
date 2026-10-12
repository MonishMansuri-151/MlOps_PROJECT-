"""
Central logging.

* Console output for development.
* One rotating file  logs/app.log  (max 5 files x 2 MB) - no new file per start.
* The logs/ folder lives inside this project folder, whatever directory the
  server is started from.
* Set LOG_LEVEL=DEBUG|INFO|WARNING in .env to change verbosity,
  LOG_TO_FILE=false to log to the console only.
"""
import logging
import os
from logging.handlers import RotatingFileHandler

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(PROJECT_DIR, "logs")
LOG_FILE_PATH = os.path.join(LOGS_DIR, "app.log")

_FORMAT = "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
_configured = False


def _configure_root() -> None:
    global _configured
    if _configured:
        return
    _configured = True

    level = getattr(
        logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO
    )
    root = logging.getLogger()
    root.setLevel(level)

    formatter = logging.Formatter(_FORMAT)

    if not any(isinstance(h, logging.StreamHandler) and
               not isinstance(h, RotatingFileHandler) for h in root.handlers):
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        root.addHandler(console)

    if os.getenv("LOG_TO_FILE", "true").lower() == "false":
        return

    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
        file_handler = RotatingFileHandler(
            LOG_FILE_PATH,
            maxBytes=2_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError:
        # Read-only disk etc.: keep running with console logging only.
        root.warning("File logging disabled (cannot write %s).", LOGS_DIR)


def get_logger(name: str = "sanjivni") -> logging.Logger:
    _configure_root()
    return logging.getLogger(name)
