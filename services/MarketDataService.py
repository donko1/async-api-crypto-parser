from config.settings import Config
from parser.parser_html import (
    get_values_from_html_to_dict,
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
        save_values_to_json(icons_json, json_path)
        logger.info("Updating icons was completed successfully")

    async def force_parse(self, json_path=None):
        """Forcing parse new data"""
        if json_path is None:
            json_path = self.config.JSON_PATH

        # Here u wright icon tester

        await get_html_for_top_100()
        save_values_to_json(
            get_values_from_html_to_dict(parse_icons_from_file=True), filepath=json_path
        )
