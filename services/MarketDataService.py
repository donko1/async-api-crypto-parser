import asyncio
from datetime import datetime, timedelta
import os

import aiohttp
from redis.asyncio import Redis
from config.settings import Config
from parser.parser_html import (
    get_values_from_html_to_dict,
    lost_icons_count,
    parse_icons,
    save_values_to_json,
)
from parser.parser_site import get_html_by_playwright, get_html_for_top_100
from core.logger import get_logger

logger = get_logger("MarketDataService")


class MarketDataService:
    def __init__(self, config: Config = None) -> None:
        if config is None:
            config = Config.load()
        self.config = config
        self.redis = Redis(
            host=self.config.REDIS_HOST,
            port=self.config.REDIS_PORT,
            db=0,
            decode_responses=True,
        )
        self.ICONS_UPDATE_LOCK_KEY = "icons:update_lock"

    async def _should_update_icons_by_time(self) -> bool:
        """Returns if need update icons by time"""
        if self.config.ICONS_BY_TIME_UPDATE:
            if not await self.redis.exists(self.ICONS_UPDATE_LOCK_KEY):
                logger.info("_should_update_icons_by_time returns True...")
                return True
        return False

    def _should_update_by_lost_icons(self, json_path=None) -> bool:
        """Returns if need update icons by too many lost"""
        if json_path is None:
            json_path = self.config.ICONS
        if os.path.exists(json_path):
            if lost_icons_count(json_path) >= self.config.MINIMUM_LOST_ICONS:
                logger.info("_should_update_by_lost_icons returns True...")
                return True
        else:
            return True

        return False

    async def test_connection(self) -> bool:
        """Returns true if connection is works and false if not"""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://coinmarketcap.com/coins/") as response:
                return response.status == 200

    async def force_update_icons(self, html_path=None, json_path=None):
        """Forcing updating icons. Downloading page with playwright and save icons to json_path"""
        if html_path is None:
            html_path = self.config.HTML_PATH

        if json_path is None:
            json_path = self.config.ICONS

        logger.info("Downloading page with playwright....")
        await get_html_by_playwright(filepath=html_path)

        logger.info("Parsing and saving icons...")
        icons_json = parse_icons(filepath=html_path)
        if self.config.ICONS_BY_TIME_UPDATE:
            logger.info("Writing update time in redis...")
            await self.redis.set(
                self.ICONS_UPDATE_LOCK_KEY,
                1,
                ex=self.config.ICONS_STORAGE_SECONDS,
                nx=True,
            )

        save_values_to_json(icons_json, json_path)
        logger.info("Updating icons was completed successfully")

    async def force_parse(self, json_path=None):
        """Forcing parse new data"""
        if json_path is None:
            json_path = self.config.JSON_PATH

        logger.info("Check if needed update icons...")
        should_update_by_time = await self._should_update_icons_by_time()

        if should_update_by_time or self._should_update_by_lost_icons(
            json_path=json_path
        ):
            await self.force_update_icons()

        await get_html_for_top_100()
        save_values_to_json(
            get_values_from_html_to_dict(parse_icons_from_file=True), filepath=json_path
        )


async def main():
    service = MarketDataService()
    await service.force_parse()


if __name__ == "__main__":
    asyncio.run(main())
