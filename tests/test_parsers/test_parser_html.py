import json
from pathlib import Path

from parser.parser_html import get_values_from_html_to_dict, save_values_to_json


def test_parse_html_to_dict_with_p():
    html_path = Path(__file__).parent.parent / "fixtures" / "p_values.html"

    result = get_values_from_html_to_dict(filepath=html_path)

    assert isinstance(result, dict)
    assert len(result) == 7

    assert "BTC" in result
    assert result["BTC"]["name"].lower().startswith("bitcoin")


def test_parse_html_to_dict_with_span():
    html_path = Path(__file__).parent.parent / "fixtures" / "span_values.html"

    result = get_values_from_html_to_dict(filepath=html_path)

    assert isinstance(result, dict)
    assert len(result) == 7

    assert "BTC" in result
    assert result["BTC"]["name"].lower().startswith("bitcoin")


def test_parse_html_to_dict_combination():
    html_path = Path(__file__).parent.parent / "fixtures" / "combination_values.html"

    result = get_values_from_html_to_dict(filepath=html_path)

    assert isinstance(result, dict)
    assert len(result) == 7

    assert "AAPL" in result
    assert result["AAPL"]["name"].lower().startswith("apple")


def test_save_values_to_json(tmp_path):
    file_path = tmp_path / "json.json"

    test_dict = {"test_key": "test_value"}
    save_values_to_json(data=test_dict, filepath=file_path)

    with open(file_path) as f:
        d = json.load(f)

    assert d == test_dict
