import asyncio
import aiofiles
import aiohttp
from config.settings import config
from core.logger import get_logger

logger = get_logger("parser_site")


async def get_html_for_top_100(filepath=config.HTML_PATH):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://coinmarketcap.com/coins/",
            headers={"User-Agent": "Mozilla/5.0"},
        ) as resp:
            logger.info(f"Status:{resp.status}")
            html = await resp.text()
            async with aiofiles.open(filepath, "w") as f:
                await f.write(html)
            logger.info("Ending writing html_file")


async def test():
    await get_html_for_top_100()
    logger.info("Successfully tested!")


if __name__ == "__main__":
    asyncio.run(test())
