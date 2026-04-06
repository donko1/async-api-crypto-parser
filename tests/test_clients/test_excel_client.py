from pathlib import Path
from unittest.mock import Mock

import pytest

from core.excel_client import ExcelClient, NoExcelFileSelected


def test_client_crashed_if_no_data(mocker, config_fixture_empty):
    # Arrange
    temp_config_mock = mocker.patch("config.settings.Config.load")
    temp_config_mock.return_value = config_fixture_empty

    # Act & Arrange
    with pytest.raises(NoExcelFileSelected, match="Excel file path is not provided"):
        client = ExcelClient()


def test_client_doesnt_crashed_if_path_include(mocker, config_fixture_filepath_excel):
    # Arrange
    temp_config_mock = mocker.patch("config.settings.Config.load")
    temp_config_mock.return_value = config_fixture_filepath_excel

    path_mock_class = mocker.patch("core.excel_client.Path")

    path_mock_class.side_effect = lambda arg: mocker.Mock(
        spec=Path, __str__=lambda s: arg
    )

    path_mock_instance = path_mock_class.return_value

    path_mock_instance.is_file.return_value = True
    path_mock_instance.exists.return_value = True

    # Act
    client_env = ExcelClient()
    client_directly = ExcelClient("direct/path")

    # Assert
    assert str(client_env.filepath) == "some/example/path"
    assert str(client_directly.filepath) == "direct/path"


def test_client_crashed_if_path_doesnt_exists(mocker, config_fixture_filepath_excel):
    # Arrange
    temp_config_mock = mocker.patch("config.settings.Config.load")
    temp_config_mock.return_value = config_fixture_filepath_excel

    # Act & Assert
    with pytest.raises(FileExistsError, match="Provided excel file doesnt exist"):
        ExcelClient()

    with pytest.raises(FileExistsError, match="Provided excel file doesnt exist"):
        ExcelClient(filepath="random/doesnt/exists/path")


def test_client__get_keys_from_dict(valid_client_excel, same_keys, diff_keys):
    # arrange
    client = valid_client_excel

    # Act
    two_keys = client._get_keys_from_dict(same_keys)
    four_keys = client._get_keys_from_dict(diff_keys)

    # Asserting getting error if arg is not dict
    with pytest.raises(TypeError, match="Method can get keys only from dictionaries!"):
        client._get_keys_from_dict(["1", "2", "3"])

    # Assert
    assert len(two_keys) == 2
    assert len(four_keys) == 4

    assert "a" in two_keys and "b" in two_keys
    assert ("a", "b", "c", "d") == four_keys


def test_client__get_letter_for_keys(valid_client_excel, abcd_keys, abcdef_keys):
    # Arrange
    client = valid_client_excel

    # Act
    keys_1 = client._get_letter_for_keys(abcd_keys)
    keys_2 = client._get_letter_for_keys(abcdef_keys)

    # Asserting getting error if arg is not dict
    with pytest.raises(
        TypeError, match=r"Keys list must be list or tuple type but got"
    ):
        client._get_letter_for_keys(None)

    # Assert
    assert len(keys_1) == 4
    assert len(keys_2) == 6
    assert keys_1["B"] == "b" == keys_2["B"]
    assert keys_2["D"] == "d"


def test_client_write_correct_mapping(mock_excel_client_self):
    # Arrange
    data = {"user_ids": [101, 102], "status": ["active", "pending"]}

    mapping = {"A": "user_ids", "B": "status"}

    # Act
    ExcelClient.write_with_columns_by_key(mock_excel_client_self, data, mapping)

    # Asserting getting error if data arg is not dict
    with pytest.raises(TypeError, match="Data must be a dictionary!"):
        ExcelClient.write_with_columns_by_key(mock_excel_client_self, None, mapping)
    with pytest.raises(TypeError, match="Columns by keys must be a dictionary!"):
        ExcelClient.write_with_columns_by_key(mock_excel_client_self, data, None)

    # Assert
    assert mock_excel_client_self.workbook.active["A1"] == 101
    assert mock_excel_client_self.workbook.active["A2"] == 102
    assert mock_excel_client_self.workbook.active["B1"] == "active"
    assert mock_excel_client_self.workbook.active["B2"] == "pending"


def test_client_write_empty_list_for_key(mock_excel_client_self):
    # Arrange
    data = {"empty_key": []}
    mapping = {"B": "empty_key"}

    # Act
    ExcelClient.write_with_columns_by_key(mock_excel_client_self, data, mapping)

    # Assert
    assert len(mock_excel_client_self.workbook.active) == 0


def test_client_generate_columns_success(mock_excel_client_self, diff_keys):
    # Arrange
    expected_keys = ("a", "b", "c", "d")
    expected_columns = {"A": "a", "B": "b", "C": "c", "D": "d"}

    mock_excel_client_self._get_keys_from_dict.return_value = expected_keys
    mock_excel_client_self._get_letter_for_keys.return_value = expected_columns

    # Act
    result = ExcelClient.generate_columns_by_keys(mock_excel_client_self, diff_keys)

    # Assert
    assert result == expected_columns
    mock_excel_client_self._get_keys_from_dict.assert_called_once_with(diff_keys)
    mock_excel_client_self._get_letter_for_keys.assert_called_once_with(expected_keys)
