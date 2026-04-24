from dataclasses import dataclass
import json
import os
from dotenv import load_dotenv
import redis

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
        }
        print(f"App config loaded: {safe_config}")


class SettingsManager:

    REDIS_KEY = "ap:settings"

    ALLOWED_KEYS = {
        "FILEPATH_EXCEL",
        "SCHEDULER_AUTOUPDATE_SECONDS",
        "ICONS_BY_TIME_UPDATE",
        "ICONS_STORAGE_SECONDS",
        "MINIMUM_LOST_ICONS",
    }

    def __init__(self, path: str = "settings.json"):
        self.path = path
        self.config = Config.load()
        self.redis = redis.Redis(
            host=self.config.REDIS_HOST,
            port=self.config.REDIS_PORT,
            decode_responses=True,
        )

    def _load_from_json(self) -> dict:
        with open(self.path, "r") as f:
            return json.load(f)

    def _ensure_redis_filled(self):
        if not self.redis.exists(self.REDIS_KEY):
            data = self._load_from_json()
            filtered = {k: v for k, v in data.items() if k in self.ALLOWED_KEYS}
            if filtered:
                self.redis.hset(self.REDIS_KEY, mapping=filtered)

    def get(self, key: str, default: any = None) -> any:
        if key not in self.ALLOWED_KEYS:
            raise ValueError(f"Unknown setting: {key}")
        self._ensure_redis_filled()
        value = self.redis.hget(self.REDIS_KEY, key)
        return value if value is not None else default

    def get_all(self) -> dict:
        self._ensure_redis_filled()
        return self.redis.hgetall(self.REDIS_KEY)

    def set(self, key: str, value: any):
        if key not in self.ALLOWED_KEYS:
            raise ValueError(f"Unknown setting: {key}")
        self.redis.hset(self.REDIS_KEY, key, value)


config = Config.load()
if __name__ == "__main__":
    config.log_config()
