from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app


def test_read_status():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200


def test_active_status():
    client = TestClient(app)
    response = client.get("/")
    assert response.json()["status"] == "active"


def test_change_setting_value_success():
    client = TestClient(app)

    with patch("app.main.SettingsManager") as mock_manager:
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance

        response = client.post(
            "/change_settings_value",
            params={"key": "FILEPATH_EXCEL", "new_value": "/new/path/to/file.xlsx"},
        )

        assert response.status_code == 200
        assert response.json() == {
            "Message": "Setting 'FILEPATH_EXCEL' updated to '/new/path/to/file.xlsx'"
        }

        mock_instance.set.assert_called_once_with(
            "FILEPATH_EXCEL", "/new/path/to/file.xlsx"
        )


def test_change_setting_value_key_error():
    client = TestClient(app)

    with patch("app.main.SettingsManager") as mock_manager:
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance

        mock_instance.set.side_effect = ValueError("Unknown setting: WRONG_KEY")

        response = client.post(
            "/change_settings_value", params={"key": "WRONG_KEY", "new_value": "123"}
        )

        assert response.status_code == 200
        assert "Key does not exist" in str(response.json())

        mock_instance.set.assert_called_once_with("WRONG_KEY", "123")
