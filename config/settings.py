from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    "Configure the app from env values"

    DEBUG: bool
    LOG_LEVEL: str
    LOG_FILE: bool
    LOG_TERMINAL: bool

    @classmethod
    def load(cls) -> "Config":
        """loads and validate configuration"""

        requires_var = ["DEBUG"]
        missing = [var for var in requires_var if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing requires env params: {missing}")

        return cls(
            DEBUG=os.getenv("DEBUG").lower() == "true",
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            LOG_FILE=os.getenv("LOG_FILE", "True").lower() == "true",
            LOG_TERMINAL=os.getenv("LOG_TERMINAL", "True").lower() == "true",
        )

    def log_config(self):
        """Security logging config (only public data)"""
        # TODO: make it with logger from core
        safe_config = {
            "DEBUG": self.DEBUG,
            "LOG_LEVEL": self.LOG_LEVEL,
            "LOG_FILE": self.LOG_FILE,
            "LOG_TERMINAL": self.LOG_TERMINAL,
        }
        print(f"App config loaded: {safe_config}")


config = Config.load()
if __name__ == "__main__":
    config.log_config()
