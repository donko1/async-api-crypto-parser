import asyncio
import json
import pytest
from unittest.mock import ANY, AsyncMock, MagicMock, Mock, patch
from services.MarketDataService import MarketDataService
import aiohttp


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


@pytest.mark.asyncio
async def test_start_parsing_when_already_running(monkeypatch):
    """Tests that start_parsing doesn't start if parsing is already running"""

    # Arrange

    service = MarketDataService()
    service._is_running = True
    mock_logger = Mock()

    monkeypatch.setattr("services.MarketDataService.logger", mock_logger)

    # Act

    await service.start_parsing()

    # Assert

    mock_logger.warning.assert_called_once_with("MarketDataService is already running")


@pytest.mark.asyncio
async def test_start_parsing_with_custom_interval(monkeypatch):
    """Tests that service starts parsing with a custom interval"""

    # Arrange
    service = MarketDataService()
    service._is_running = False
    service._stop_event = Mock()
    service._run_periodically = AsyncMock()

    mock_create_task = Mock()
    mock_logger = Mock()

    monkeypatch.setattr(asyncio, "create_task", mock_create_task)
    monkeypatch.setattr("services.MarketDataService.logger", mock_logger)

    custom_interval = 30.5

    # Act
    await service.start_parsing(seconds_parsing=custom_interval)

    # Assert
    assert service._is_running is True
    service._stop_event.clear.assert_called_once()

    service._run_periodically.assert_called_once_with(custom_interval)

    mock_create_task.assert_called_once_with(
        ANY,
        name="MarketDataServiceTask_scheduler",
    )

    assert service._task == mock_create_task.return_value

    mock_logger.info.assert_called_once_with(
        "MarketDataService started with interval %s seconds",
        custom_interval,
    )


@pytest.mark.asyncio
async def test_stop_parsing_when_not_running(monkeypatch):
    """Tests that stop_parsing doesn't stop if parsing is not running"""

    # Arrange

    service = MarketDataService()
    service._is_running = False
    mock_logger = Mock()

    monkeypatch.setattr("services.MarketDataService.logger", mock_logger)

    # Act

    await service.stop_parsing()

    # Assert

    mock_logger.warning.assert_called_once_with("MarketDataService is not running")


@pytest.mark.asyncio
async def test_stop_parsing_when_running():
    """Tests that stop_parsing stops the parsing task when it's running"""

    # Arrange
    service = MarketDataService()
    service._is_running = True
    service._stop_event = asyncio.Event()

    task = asyncio.create_task(asyncio.sleep(10))
    service._task = task

    # Act
    await service.stop_parsing()

    # Assert

    assert task.cancelled()
    assert service._is_running is False
    assert service._stop_event.is_set()


@pytest.mark.asyncio
async def test_run_run_periodically_will_not_run_if_stop_event():
    """
    Ensures that `_run_periodically` exits immediately and does not call
    `force_parse` if `_stop_event` is already set before execution starts.

    The service instance is created via `__new__` to avoid side effects
    from `__init__` (e.g., external connections or event loop binding),
    keeping the test fully isolated and deterministic.
    """

    # Arrange
    service = MarketDataService.__new__(MarketDataService)
    service._stop_event = asyncio.Event()
    service._stop_event.set()
    service.force_parse = Mock()

    # Act
    await service._run_periodically(seconds_parsing=5.0)

    # Assert
    service.force_parse.assert_not_called()


@pytest.mark.asyncio
async def test_run_periodically_calls_force_parse_successfully(monkeypatch):
    """
    Ensures that _run_periodically calls force_parse and handles the loop correctly.
    We monkeypatch the method to stop the loop after the first call.
    """
    # Arrange
    service = MarketDataService()
    service._stop_event = asyncio.Event()
    mock_force_parse = AsyncMock()

    async def side_effect():
        service._stop_event.set()

    mock_force_parse.side_effect = side_effect

    monkeypatch.setattr(service, "force_parse", mock_force_parse)

    # Act
    await service._run_periodically(seconds_parsing=0.01)

    # Assert
    mock_force_parse.assert_called_once()


@pytest.mark.asyncio
async def test_run_periodically_resilient_to_errors(monkeypatch):
    """
    Ensures the loop continues even if force_parse raises an exception.
    """

    # Arrange
    service = MarketDataService()
    service._stop_event = asyncio.Event()

    call_info = {"count": 0}

    async def manual_mock():
        call_info["count"] += 1
        if call_info["count"] == 1:
            raise Exception("Parsing failed")
        service._stop_event.set()

    monkeypatch.setattr(service, "force_parse", manual_mock)

    # Act
    await service._run_periodically(seconds_parsing=0.001)

    # Assert
    assert call_info["count"] == 2


@pytest.mark.asyncio
async def test_close_service_closes_redis():
    """Tests that redis will close at the same time as MarketDataService"""

    # Arrange
    service = MarketDataService()
    service.redis = AsyncMock()

    # Act
    await service.close()

    # Assert
    service.redis.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session():
    """Tests that _get_session method returns aiohttp.ClientSession"""

    # Arrange
    service = MarketDataService()

    # Act
    session = await service._get_session()
    await service.close()  # Ensure we close the session after the test

    # Assert
    assert isinstance(session, aiohttp.ClientSession)
    assert not session.closed
