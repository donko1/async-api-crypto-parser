import logging
import sys
from pathlib import Path
from config.settings import config


class SimpleLogger:
    """Base logger in files and terminal"""

    def __init__(self):
        self.config = config
        self._setup()

    def _setup(self):
        """Base setup"""

        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        self.formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def get_logger(self, name: str = "app"):
        """Get named logger"""
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, self.config.LOG_LEVEL))

        if logger.handlers:
            return logger

        if self.config.LOG_TERMINAL:
            terminal_handler = logging.StreamHandler(sys.stdout)
            terminal_handler.setLevel(getattr(logging, self.config.LOG_LEVEL))
            terminal_handler.setFormatter(self.formatter)
            logger.addHandler(terminal_handler)

        if self.config.LOG_FILE:
            file_handler = logging.FileHandler(
                filename=Path("logs") / "logs.log", encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(self.formatter)
            logger.addHandler(file_handler)

        logger.propagate = False

        return logger


_logger = SimpleLogger()
get_logger = _logger.get_logger
