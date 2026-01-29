import json
from pathlib import Path

from parser.parser_html import (
    get_values_from_html_to_dict,
    save_values_to_json,
    parse_icons,
    lost_icons_count,
)


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
