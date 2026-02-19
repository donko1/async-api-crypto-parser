import asyncio
from datetime import datetime, timedelta
import os
import time
from types import NoneType
from typing import Optional

import aiohttp
import playwright
from playwright.async_api import async_playwright
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
        self._task: Optional[asyncio.Task] = None
        self.ICONS_UPDATE_LOCK_KEY = "icons:update_lock"
        self._is_running = False
        self._session: Optional[aiohttp.ClientSession] = None
        self._stop_event = asyncio.Event()

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

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
        session = await self._get_session()
        async with session.get("https://coinmarketcap.com/coins/") as response:
            return response.status == 200

    async def _playwright_request(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            response = await page.goto(
                "https://coinmarketcap.com/coins/", wait_until="domcontentloaded"
            )
            status = response.status
            await browser.close()
            return status

    async def _aiohttp_request(self):
        session = await self._get_session()
        async with session.get("https://coinmarketcap.com/coins/") as response:
            return response.status

    async def estimate_parse_time(self) -> dict:
        """Calculating how much need to connect with aiohttp and playwright
        Returnable dict:
        {
        "playwright":
            { "status": *status_code*,
              "duration": *duration in seconds* },
        "aiohttp":
          { "status": *status_code*,
          "duration": *duration in seconds* }
        }"""
        start = time.time()
        status_playwright = await self._playwright_request()
        time_playwright = time.time() - start

        start = time.time()
        status_aiohttp = await self._aiohttp_request()
        time_aiohttp = time.time() - start

        out = {
            "playwright": {
                "status": status_playwright,
                "duration": time_playwright,
            },
            "aiohttp": {
                "status": status_aiohttp,
                "duration": time_aiohttp,
            },
        }

        logger.info(out)

        return out

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
            try:
                await self.force_update_icons()
            except Exception as _ex:
                logger.error(f"force update icons failed: {_ex}")

        try:
            await get_html_for_top_100()
            save_values_to_json(
                get_values_from_html_to_dict(parse_icons_from_file=True),
                filepath=json_path,
            )
        except Exception as _ex:
            logger.error(f"force parse failed: {_ex}")
            return

    async def start_parsing(self, seconds_parsing: float | NoneType = None) -> None:
        """Starts parsing by scheduler"""
        if self._is_running:
            logger.warning("MarketDataService is already running")
            return

        if seconds_parsing is None:
            seconds_parsing = self.config.SCHEDULER_AUTOUPDATE_SECONDS

        self._is_running = True

        self._stop_event.clear()

        self._task = asyncio.create_task(
            self._run_periodically(seconds_parsing),
            name="MarketDataServiceTask_scheduler",
        )

        logger.info(
            "MarketDataService started with interval %s seconds", seconds_parsing
        )

    async def _run_periodically(self, seconds_parsing: float) -> None:
        """Runs the parsing task periodically"""
        while not self._stop_event.is_set():
            start_time = datetime.now()
            try:
                await self.force_parse()
            except Exception as e:
                logger.error("Error during parsing: %s", e)
                await asyncio.sleep(seconds_parsing)

            elapsed_time = (datetime.now() - start_time).total_seconds()
            sleep_time = max(0, seconds_parsing - elapsed_time)
            logger.info("Sleeping for %s seconds before next parsing...", sleep_time)
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=sleep_time)
            except asyncio.TimeoutError:
                pass

    async def stop_parsing(self) -> None:
        """Stops parsing by scheduler"""
        if not self._is_running:
            logger.warning("MarketDataService is not running")
            return

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                logger.info("MarketDataService task cancelled successfully")

        self._is_running = False
        self._stop_event.set()

        logger.info("MarketDataService stopped")

    async def close(self) -> None:
        """Closes all sessions and connections"""
        logger.info("MarketData service is closing...")
        await self.redis.aclose()
        await self._session.close() if self._session else None
        logger.info("MarketData service closed successfully!")


async def main():
    service = MarketDataService()
    await service.start_parsing()
    await asyncio.sleep(150)
    await service.stop_parsing()


if __name__ == "__main__":
    asyncio.run(main())
