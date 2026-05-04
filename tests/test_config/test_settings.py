import pytest
import json
from unittest.mock import patch, mock_open


def test_get_value_from_redis(settings_manager, mock_redis):
    mock_redis.exists.return_value = True
    mock_redis.hget.return_value = "my_path.xlsx"

    val = settings_manager.get("FILEPATH_EXCEL")

    assert val == "my_path.xlsx"
    mock_redis.hget.assert_called_with("ap:settings", "FILEPATH_EXCEL")


def test_get_invalid_key(settings_manager):
    with pytest.raises(ValueError, match="Unknown setting: INVALID"):
        settings_manager.get("INVALID")


def test_ensure_redis_filled_when_empty(settings_manager, mock_redis):
    json_data = {"FILEPATH_EXCEL": "data.xlsx", "OTHER": "ignore"}
    mock_redis.exists.return_value = False

    with patch("builtins.open", mock_open(read_data=json.dumps(json_data))), patch(
        "os.path.exists", return_value=True
    ):
        settings_manager._ensure_redis_filled()

    mock_redis.hset.assert_called_with(
        "ap:settings", mapping={"FILEPATH_EXCEL": "data.xlsx"}
    )


def test_set_value(settings_manager, mock_redis):
    settings_manager.set("SCHEDULER_AUTOUPDATE_SECONDS", 60)

    mock_redis.hset.assert_called_with(
        "ap:settings", "SCHEDULER_AUTOUPDATE_SECONDS", "60"
    )


def test_get_all(settings_manager, mock_redis):
    mock_redis.exists.return_value = True
    mock_redis.hgetall.return_value = {"FILEPATH_EXCEL": "data.xlsx"}

    result = settings_manager.get_all()

    assert result == {"FILEPATH_EXCEL": "data.xlsx"}
    mock_redis.hgetall.assert_called_once_with("ap:settings")
