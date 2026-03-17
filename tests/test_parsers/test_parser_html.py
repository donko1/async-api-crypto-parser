from datetime import datetime
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from parser.parser_html import (
    get_price_in_value,
    get_values_from_html_to_dict,
    save_values_to_json,
    parse_icons,
    lost_icons_count,
)
from tests.test_parsers.conftest import some_coin_data


def test_parse_html_to_dict_with_p():
    html_path = Path(__file__).parent.parent / "fixtures" / "p_values.html"

    result = get_values_from_html_to_dict(filepath=html_path)

    assert isinstance(result, dict)
    assert len(result) == 7

    assert "BTC" in result
    assert result["BTC"]["name"].lower().startswith("bitcoin")
    assert result["BTC"]["icon"].startswith("https://")
    assert isinstance(result["BTC"]["price"], float)


def test_parse_html_to_dict_with_span():
    html_path = Path(__file__).parent.parent / "fixtures" / "span_values.html"

    result = get_values_from_html_to_dict(filepath=html_path)

    assert isinstance(result, dict)
    assert len(result) == 7

    assert "BTC" in result
    assert result["BTC"]["name"].lower().startswith("bitcoin")
    assert result["BTC"]["icon"].startswith("https://")
    assert isinstance(result["BTC"]["price"], float)


def test_parse_html_to_dict_combination():
    html_path = Path(__file__).parent.parent / "fixtures" / "combination_values.html"

    result = get_values_from_html_to_dict(filepath=html_path)

    assert isinstance(result, dict)
    assert len(result) == 7

    assert "AAPL" in result
    assert result["AAPL"]["name"].lower().startswith("apple")
    assert result["AAPL"]["icon"].startswith("https://")
    assert isinstance(result["AAPL"]["price"], float)


def test_save_values_to_json(tmp_path):
    file_path = tmp_path / "json.json"

    test_dict = {"test_key": "test_value"}
    save_values_to_json(data=test_dict, filepath=file_path)

    with open(file_path) as f:
        d = json.load(f)

    assert d == test_dict


def test_parse_icons():
    html_path = Path(__file__).parent.parent / "fixtures" / "combination_values.html"

    result = parse_icons(filepath=html_path)

    assert "META" not in result
    assert "NVDA" in result
    assert len(result) == 6
    assert result["TSLA"] == "https://example.com/"


def test_lost_icons():
    html_path = Path(__file__).parent.parent / "fixtures" / "lost_icons.json"

    result = lost_icons_count(filepath=html_path)

    assert 3 == result


def test_parse_html_lost_change_1hr(monkeypatch):
    # Arrange
    html_path = Path(__file__).parent.parent / "fixtures" / "combination_values.html"

    mock_logger = Mock()

    monkeypatch.setattr("parser.parser_html.logger", mock_logger)

    # Act
    result = get_values_from_html_to_dict(filepath=html_path)

    # Assert
    mock_logger.info.assert_called_with("change_1hr was lost 6")

    assert result["NVDA"]["change_1hr"] == 0
    assert result["TSLA"]["change_1hr"] == 0.25


def test_parse_html_with_all_1hr(monkeypatch):
    # Arrange
    html_path = Path(__file__).parent.parent / "fixtures" / "all_changed_1hr.html"

    mock_logger = Mock()

    monkeypatch.setattr("parser.parser_html.logger", mock_logger)

    # Act
    result = get_values_from_html_to_dict(filepath=html_path)

    # Assert
    mock_logger.assert_not_called()

    assert result["AMZN"]["change_1hr"] == 5 / 100
    assert result["MSFT"]["change_1hr"] == 10 / 100


def test_get_price_in_value_correct(some_coin_data):
    # Arrange
    data = some_coin_data

    # Act
    usd_anon_price = get_price_in_value(data)
    eth_price = get_price_in_value(data, "ETH")
    btc_price = get_price_in_value(data, "BTC")
    usd_price = get_price_in_value(data, "USD")

    # Assert
    assert usd_price == usd_anon_price
    assert usd_price["price"] == 52
    assert btc_price["price"] == 42
    assert eth_price["price"] == 69


def test_raise_exception_in_get_price_in_value_if_value_doesnt_exists(some_coin_data):
    # Arrange
    data = some_coin_data

    # Act
    with pytest.raises(Exception) as exc_info:
        get_price_in_value(data, "UNKNOWN")

    # Assert
    assert "This value doesnt available" in str(exc_info.value)


def test_get_price_in_value_correct(coin_data_expanded):
    # Arrange
    data = coin_data_expanded

    # Act
    usd_anon_price = get_price_in_value(data)
    eth_price = get_price_in_value(data, "ETH")
    btc_price = get_price_in_value(data, "BTC")
    usd_price = get_price_in_value(data, "USD")

    # Assert
    assert usd_price == usd_anon_price
    assert usd_price["price"] == 35.092
    assert btc_price["price"] == 0.0005
    assert eth_price["price"] == 0.017105

    assert (
        usd_price["percentChange30d"]
        == btc_price["percentChange30d"]
        == eth_price["percentChange30d"]
    )

    assert (
        usd_price["percentChange1y"]
        == btc_price["percentChange1y"]
        == eth_price["percentChange1y"]
    )

    assert usd_price["lastUpdated"] == "2026-03-06T12:04:00.000Z"

    datetime_object = datetime.strptime(
        usd_price["lastUpdated"], "%Y-%m-%dT%H:%M:%S.%fZ"
    )

    assert datetime_object.year == 2026
    assert datetime_object.month == 3
    assert datetime_object.day == 6
