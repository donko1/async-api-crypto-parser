import json
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


@pytest.mark.asyncio
@pytest.mark.network
async def test_force_parse(tmp_path):
    """Tests that force_parse writes current data in json"""

    json_path = tmp_path / "json.json"

    Service = MarketDataService()

    await Service.force_parse(json_path)

    with open(json_path) as f:
        out = json.load(f)

    assert len(out) == 100
    assert "BTC" in out.keys()
    for key in ["price", "id", "icon"]:
        assert key in out["BTC"].keys()
    assert isinstance(out["BTC"]["price"], float)
