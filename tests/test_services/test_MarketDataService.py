import asyncio
import json
import time
import playwright
import pytest
from unittest.mock import AsyncMock, Mock, patch
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


@pytest.mark.asyncio
async def test_should_update_icons_by_time_true():
    service = MarketDataService()
    service.config = Mock()
    service.config.ICONS_BY_TIME_UPDATE = True

    service.redis = Mock()
    service.redis.exists = AsyncMock(return_value=False)

    result = await service._should_update_icons_by_time()

    assert result is True


@pytest.mark.asyncio
async def test_should_update_icons_by_time_false():
    service = MarketDataService()
    service.config = Mock()
    service.config.ICONS_BY_TIME_UPDATE = True

    service.redis = Mock()
    service.redis.exists = AsyncMock(return_value=True)

    result = await service._should_update_icons_by_time()

    assert result is False


def test_should_update_by_lost_icons_true(monkeypatch):
    service = MarketDataService()
    service.config = Mock()
    service.config.MINIMUM_LOST_ICONS = 5

    monkeypatch.setattr("os.path.exists", lambda _: True)
    monkeypatch.setattr("services.MarketDataService.lost_icons_count", lambda _: 15)

    result = service._should_update_by_lost_icons("dummy_path")

    assert result is True


def test_should_update_by_lost_icons_false(monkeypatch):
    service = MarketDataService()
    service.config = Mock()
    service.config.MINIMUM_LOST_ICONS = 5

    monkeypatch.setattr("os.path.exists", lambda _: True)
    monkeypatch.setattr("services.MarketDataService.lost_icons_count", lambda _: 3)

    result = service._should_update_by_lost_icons("dumb_path")

    assert result is False


def test_should_update_by_lost_doesnt_fail(monkeypatch):
    service = MarketDataService()
    service.config = Mock()
    service.MINIMUM_LOST_ICONS = 5

    monkeypatch.setattr("os.path.exists", lambda _: False)

    result = service._should_update_by_lost_icons("dumb_path")

    assert result is True


@pytest.mark.asyncio
async def test_test_connection():
    service = MarketDataService()

    mock_response = AsyncMock()

    mock_response.status = 200
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        result = await service.test_connection()
        assert result is True

    mock_response.status = 500
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_response
        result = await service.test_connection()
        assert result is False


@pytest.mark.asyncio
async def test_estimate_parse_time(monkeypatch):
    service = MarketDataService()

    async def playwright_mock():
        await asyncio.sleep(7.5)
        return 200

    async def aiohttp_mock():
        await asyncio.sleep(1.5)
        return 200

    monkeypatch.setattr(service, "_playwright_request", playwright_mock)
    monkeypatch.setattr(service, "_aiohttp_request", aiohttp_mock)

    result = await service.estimate_parse_time()

    assert result["playwright"]["status"] == 200
    assert result["aiohttp"]["status"] == 200

    assert 7.3 <= result["playwright"]["duration"] <= 7.7
    assert 1.3 <= result["aiohttp"]["duration"] <= 1.7
