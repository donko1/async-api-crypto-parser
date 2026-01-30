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
    HTML_PATH: str
    JSON_PATH: str
    ICONS: str
    ICONS_BY_TIME_UPDATE: bool
    ICONS_STORAGE_SECONDS: int
    MINIMUM_LOST_ICONS: int
    REDIS_HOST: str
    REDIS_PORT: int

    @classmethod
    def load(cls) -> "Config":
        """loads and validate configuration"""

        requires_var = ["DEBUG"]
        missing = [var for var in requires_var if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing requires env params: {missing}")

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        return cls(
            DEBUG=os.getenv("DEBUG").lower() == "true",
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            LOG_FILE=os.getenv("LOG_FILE", "True").lower() == "true",
            LOG_TERMINAL=os.getenv("LOG_TERMINAL", "True").lower() == "true",
            HTML_PATH=os.path.join(
                base_dir, "html_cache", os.getenv("HTML_PATH", "html_cache.html")
            ),
            JSON_PATH=os.path.join(
                base_dir, "json_cache", os.getenv("JSON_PATH", "json_coins.json")
            ),
            ICONS=os.path.join(
                base_dir, "json_cache", os.getenv("ICONS", "icons.json")
            ),
            ICONS_BY_TIME_UPDATE=os.getenv("ICONS_BY_TIME_UPDATE", "False").lower()
            == "true",
            ICONS_STORAGE_SECONDS=int(os.getenv("ICONS_STORAGE_SECONDS", "3600")),
            MINIMUM_LOST_ICONS=int(os.getenv("MINIMUM_LOST_ICONS", "5")),
            REDIS_HOST=os.getenv("REDIS_HOST", "localhost"),
            REDIS_PORT=int(
                os.getenv("REDIS_PORT", "6379"),
            ),
        )

    def log_config(self):
        """Security logging config (only public data)"""
        safe_config = {
            "DEBUG": self.DEBUG,
            "LOG_LEVEL": self.LOG_LEVEL,
            "LOG_FILE": self.LOG_FILE,
            "LOG_TERMINAL": self.LOG_TERMINAL,
            "ICONS_BY_TIME_UPDATE": self.ICONS_BY_TIME_UPDATE,
            "ICONS_STORAGE_SECONDS": self.ICONS_STORAGE_SECONDS,
            "MINIMUM_LOST_ICONS": self.MINIMUM_LOST_ICONS,
        }
        print(f"App config loaded: {safe_config}")


config = Config.load()
if __name__ == "__main__":
    config.log_config()
