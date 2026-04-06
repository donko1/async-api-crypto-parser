from collections import namedtuple
from unittest.mock import MagicMock

import pytest

from core.excel_client import ExcelClient


@pytest.fixture
def config_fixture_empty():
    config = namedtuple("Config", ["FILEPATH_EXCEL"])
    c = config("")
    return c


@pytest.fixture
def config_fixture_filepath_excel():
    config = namedtuple("Config", ["FILEPATH_EXCEL"])
    c = config("some/example/path")
    return c


@pytest.fixture
def valid_client_excel(tmp_path):
    file_path = tmp_path / "example.xlsx"
    file_path.touch()

    return ExcelClient(filepath=file_path)


@pytest.fixture
def same_keys():
    return {
        "1": {"a": "lorem", "b": "ipsum"},
        "2": {"a": "non_lorem", "b": "non_ipsum"},
    }


@pytest.fixture
def diff_keys():
    return {
        "1": {"a": "lorem"},
        "2": {"b": "ipsum", "c": "non_lorem", "d": "non_ipsum"},
    }


@pytest.fixture
def abcd_keys():
    return ("a", "b", "c", "d")


@pytest.fixture
def abcdef_keys():
    return ["a", "b", "c", "d", "e", "f"]


@pytest.fixture
def mock_excel_client_self():
    client = MagicMock()

    client.workbook = MagicMock()
    client.workbook.active = {}

    return client
