import asyncio
import aiofiles
import aiohttp
import os

main = __name__ == "__main__"
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(base_dir, "html_cache", f"html_cache.html")


async def get_html_for_top_100():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://coinmarketcap.com/coins/",
            headers={"User-Agent": "Mozilla/5.0"},
        ) as resp:
            if main:
                print("Status:", resp.status)
            html = await resp.text()
            async with aiofiles.open(file_path, "w") as f:
                await f.write(html)


async def test():
    await get_html_for_top_100()


if main:
    asyncio.run(test())
