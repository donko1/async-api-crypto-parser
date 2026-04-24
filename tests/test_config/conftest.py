import pytest
import json
from unittest.mock import MagicMock, patch, mock_open
from config.settings import SettingsManager


@pytest.fixture
def mock_redis():
    return MagicMock()


@pytest.fixture
def mock_config():
    with patch("config.settings.Config") as mocked_config:
        mocked_config.load.return_value = MagicMock(
            REDIS_HOST="localhost", REDIS_PORT=6379
        )
        yield mocked_config


@pytest.fixture
def settings_manager(mock_redis, mock_config):
    with patch("redis.Redis", return_value=mock_redis):
        return SettingsManager(path="test_settings.json")
