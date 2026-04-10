from pathlib import Path
import string

from openpyxl import load_workbook

from config.settings import Config
from core.logger import get_logger

logger = get_logger("excel_client")


class NoExcelFileSelected(Exception):
    """Raised when no Excel file path is provided."""

    pass


class ExcelClient:
    def __init__(self, filepath=None):
        config = Config.load()
        if filepath is None:
            if config.FILEPATH_EXCEL:
                self.filepath = Path(config.FILEPATH_EXCEL)
            else:
                raise NoExcelFileSelected("Excel file path is not provided")
        else:
            self.filepath = Path(filepath)

        if not self.filepath.is_file():
            raise FileExistsError("Provided excel file doesnt exist")

        logger.info("File found successfully!")

    def open(self):
        logger.info("Open workbook...")
        self.workbook = load_workbook(self.filepath)

    def _get_keys_from_dict(self, d: dict):
        if not isinstance(d, dict):
            raise TypeError("Method can get keys only from dictionaries!")

        keys_out = []
        for _, value in d.items():
            for k in tuple(value.keys()):
                if k not in keys_out:
                    keys_out.append(k)

        return tuple(keys_out)

    def _get_letter_for_keys(self, keys: tuple | list):
        if not isinstance(keys, (list, tuple)):
            raise TypeError(
                f"Keys list must be list or tuple type but got {type(keys)}!"
            )

        columns = string.ascii_uppercase
        out_d = {}

        for i, el in enumerate(keys):
            out_d[columns[i]] = el

        logger.info(f"Generated columns for keys: {out_d}")
        return out_d

    def write_with_columns_by_key(
        self, data: dict, columns_by_keys: dict, header: bool = True
    ):

        if not isinstance(data, dict):
            raise TypeError("Data must be a dictionary!")
        if not isinstance(columns_by_keys, dict):
            raise TypeError("Columns by keys must be a dictionary!")

        if header:
            for column, key in columns_by_keys.items():
                self.workbook.active[f"{column}1"] = key

        for row_index, crypto_data in enumerate(data.values(), start=1):
            for column, key in columns_by_keys.items():
                value = crypto_data.get(key, "")
                index = row_index + 1 if header else row_index
                self.workbook.active[f"{column}{index}"] = value

    def generate_columns_by_keys(self, data: dict):
        if not isinstance(data, dict):
            raise TypeError("Data must be a dictionary!")

        keys = self._get_keys_from_dict(data)
        return self._get_letter_for_keys(keys)

    def close(self):
        logger.info("Close workbook...")
        self.workbook.save(self.filepath)


def main():
    client = ExcelClient()
    client.open()
    data = {
        "BTC": {"price": 50000, "volume": 1000},
        "ETH": {"price": 4000, "volume": 500},
    }
    columns_by_keys = client.generate_columns_by_keys(data)
    client.write_with_columns_by_key(data, columns_by_keys)
    client.close()


if __name__ == "__main__":
    main()
