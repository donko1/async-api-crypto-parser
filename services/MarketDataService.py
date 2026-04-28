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
from config.settings import Config, SettingsManager
from core.excel_client import ExcelClient
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
        self.settings = SettingsManager()
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

        try:
            self.excel_client = ExcelClient(filepath=self.config.get("FILEPATH_EXCEL"))
            self.can_write_in_excel = True
        except Exception as e:
            logger.error("Error while initializing excel client: %s", e)
            self.can_write_in_excel = False

    def _get_data(self) -> dict:
        """Getting data from json file"""
        if os.path.exists(self.config.JSON_PATH):
            with open(self.config.JSON_PATH, "r") as f:
                return get_values_from_html_to_dict(parse_icons_from_file=True)
        else:
            logger.warning(f"Json file {self.config.JSON_PATH} does not exist!")
            return {}

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _should_update_icons_by_time(self) -> bool:
        """Returns if need update icons by time"""
        if self.settings.get("ICONS_BY_TIME_UPDATE"):
            if not await self.redis.exists(self.ICONS_UPDATE_LOCK_KEY):
                logger.info("_should_update_icons_by_time returns True...")
                return True
        return False

    def _should_update_by_lost_icons(self, json_path=None) -> bool:
        """Returns if need update icons by too many lost"""
        if json_path is None:
            json_path = self.config.ICONS
        if os.path.exists(json_path):
            if lost_icons_count(json_path) >= self.settings.get("MINIMUM_LOST_ICONS"):
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
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                response = await page.goto(
                    "https://coinmarketcap.com/coins/", wait_until="domcontentloaded"
                )
                status = response.status
                await browser.close()
                return status
        except Exception as _ex:
            logger.error(f"_playwright_request failed by {_ex}")
            return 500

    async def _aiohttp_request(self):
        try:
            session = await self._get_session()
            async with session.get("https://coinmarketcap.com/coins/") as response:
                return response.status
        except Exception as _ex:
            logger.error(f"_aiohttp_request failed by {_ex}")
            return 500

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
        try:
            await get_html_by_playwright(filepath=html_path)
        except Exception as _ex:
            logger.error("Error while opening url with playwright")
            return

        logger.info("Parsing and saving icons...")
        icons_json = parse_icons(filepath=html_path)
        if self.settings.get("ICONS_BY_TIME_UPDATE"):
            logger.info("Writing update time in redis...")
            await self.redis.set(
                self.ICONS_UPDATE_LOCK_KEY,
                1,
                ex=self.settings.get("ICONS_STORAGE_SECONDS"),
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

    async def start_parsing(
        self, seconds_parsing: float | NoneType = None, writing_in_excel: bool = False
    ) -> None:
        """Starts parsing by scheduler"""
        if self._is_running:
            logger.warning("MarketDataService is already running")
            return

        if seconds_parsing is None:
            seconds_parsing = self.settings.get("SCHEDULER_AUTOUPDATE_SECONDS")

        self._is_running = True

        self._stop_event.clear()

        self._task = asyncio.create_task(
            self._run_periodically(seconds_parsing, writing_in_excel=writing_in_excel),
            name="MarketDataServiceTask_scheduler",
        )

        logger.info(
            "MarketDataService started with interval %s seconds", seconds_parsing
        )

    async def _run_periodically(
        self, seconds_parsing: float, writing_in_excel: bool = False
    ) -> None:
        """Runs the parsing task periodically"""
        while not self._stop_event.is_set():
            start_time = datetime.now()

            self.next_run_at = datetime.now() + timedelta(seconds=seconds_parsing)

            try:
                await self.force_parse()
            except Exception as e:
                logger.error("Error during parsing: %s", e)
                await asyncio.sleep(seconds_parsing)

            elapsed_time = (datetime.now() - start_time).total_seconds()
            sleep_time = max(0, seconds_parsing - elapsed_time)
            logger.info("Sleeping for %s seconds before next parsing...", sleep_time)
            if writing_in_excel and self.can_write_in_excel:
                logger.info("Writing values to excel...")
                try:
                    if (
                        self.settings.get("FILEPATH_EXCEL")
                        != self.excel_client.filepath
                    ):
                        logger.info(
                            "Excel filepath changed, reinitializing excel client..."
                        )
                        self.excel_client.close()
                        self.excel_client = ExcelClient(
                            filepath=self.settings.get("FILEPATH_EXCEL")
                        )
                    self.excel_client.open()
                    data = self._get_data()
                    columns_by_keys = self.excel_client._get_letter_for_keys(
                        self.excel_client._get_keys_from_dict(data)
                    )
                    self.excel_client.write_with_columns_by_key(
                        data=data, columns_by_keys=columns_by_keys
                    )
                    self.excel_client.close()
                    logger.info("Values were written to excel successfully!")
                except Exception as e:
                    logger.error("Error while writing to excel file: %s", e)

            if writing_in_excel and not self.can_write_in_excel:
                logger.warning(
                    "Cannot write in excel because excel client was not initialized successfully"
                )

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=sleep_time)
            except asyncio.TimeoutError:
                pass

    @property
    def time_until_next_parse(self) -> float:
        """
        Every time called calculating difference between
        planed time and now
        """
        if not hasattr(self, "next_run_at"):
            return 0.0

        remaining = (self.next_run_at - datetime.now()).total_seconds()
        return max(0.0, remaining)

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

    def get_status(self) -> dict:
        """Returning status of running parser"""
        logger.info("Requested for status...")
        running = self._is_running
        next_parse = self.time_until_next_parse
        return {
            "opened": True,
            "running": running,
            "next_parse": next_parse,
            "status": "OK",
        }

    async def close(self) -> None:
        """Closes all sessions and connections"""
        logger.info("MarketData service is closing...")
        await self.redis.aclose()
        await self._session.close() if self._session else None
        logger.info("MarketData service closed successfully!")


async def main():
    service = MarketDataService()
    await service.start_parsing(writing_in_excel=True)
    await asyncio.sleep(150)
    await service.stop_parsing()


if __name__ == "__main__":
    asyncio.run(main())
