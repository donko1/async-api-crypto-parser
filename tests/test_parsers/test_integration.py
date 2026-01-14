import json
import pytest

from parser.parser_html import get_values_from_html_to_dict, save_values_to_json
from parser.parser_site import get_html_for_top_100


@pytest.mark.network
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_parsing_pipeline(tmp_path):
    html_path = tmp_path / "site.html"
    json_path = tmp_path / "json.json"
    await get_html_for_top_100(filepath=str(html_path))

    result = get_values_from_html_to_dict(filepath=str(html_path))
    save_values_to_json(result, filepath=str(json_path))

    with open(json_path) as f:
        data = json.load(f)

    assert len(data) == 100
    assert data["BTC"]["name"].lower().startswith("bitcoin")
