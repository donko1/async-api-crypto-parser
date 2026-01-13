import pytest

from parser.parser_site import get_html_for_top_100


@pytest.mark.network
@pytest.mark.asyncio
async def test_real_download_html(tmp_path):
    """Tests that html is downloaded and saved to a file."""
    file_path = tmp_path / "site.html"

    await get_html_for_top_100(filepath=str(file_path))

    content = file_path.read_text()
    assert "<html" in content.lower()


@pytest.mark.network
@pytest.mark.asyncio
async def test_non_blocked_html(tmp_path):
    """Tests that html is downloaded and html is not blocked."""
    file_path = tmp_path / "site.html"

    await get_html_for_top_100(filepath=str(file_path))

    content = file_path.read_text()
    assert "access to this site is denied" not in content.lower()
    assert "are you a robot" not in content.lower()
    assert "forbidden" not in content.lower()
    assert "bitcoin" in content.lower()  # A keyword expected to be on the page
