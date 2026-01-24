import json
import aiofiles
import pytest
from services.MarketDataService import MarketDataService


@pytest.mark.network
@pytest.mark.asyncio
async def test_force_update_icons(tmp_path):
    """Tests that force updating icons if working"""
    html_playwright_path = tmp_path / "html.html"
    icons_json = tmp_path / "icons.json"

    Service = MarketDataService()

    await Service.force_update_icons(
        html_path=html_playwright_path, json_path=icons_json
    )

    with open(icons_json) as f:
        out = json.load(f)

    assert "BTC" in out
    assert "NVDA" not in out
    assert len(out) == 100
