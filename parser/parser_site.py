import asyncio
import aiofiles
import aiohttp
from config.settings import config
from playwright.async_api import async_playwright
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


async def get_html_by_playwright(filepath=config.HTML_PATH):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        resp = await page.goto(
            "https://coinmarketcap.com/coins/", wait_until="domcontentloaded"
        )

        scroll_height = await page.evaluate("document.body.scrollHeight")
        step = scroll_height / 8

        for i in range(1, 9):
            target_scroll = step * i
            await page.evaluate(f"window.scrollTo(0, {target_scroll})")
            await asyncio.sleep(0.5)

        html = await page.content()

        logger.info(f"Status:{resp.status}")

        await browser.close()

    async with aiofiles.open(filepath, "w") as f:
        await f.write(html)
        logger.info("Ending writing html_file")


async def test():
    await get_html_by_playwright()
    logger.info("Successfully downloaded with no errors!")


if __name__ == "__main__":
    asyncio.run(test())
