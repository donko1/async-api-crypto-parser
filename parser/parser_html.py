import json
from selectolax.parser import HTMLParser
from config.settings import config
from core.logger import get_logger

logger = get_logger("parser_html")


def get_values_from_html_to_dict(
    filepath=config.HTML_PATH, parse_icons_from_file=False, icons_path=config.ICONS
):
    with open(filepath) as f:
        html = f.read()

    tree = HTMLParser(html)
    trs = tree.css("tr")[2::]

    out = {}

    logger.info(f"Found {len(trs)} tr's...")

    if parse_icons_from_file:
        with open(icons_path) as f:
            icons = json.load(f)

    for i, tr in enumerate(trs):
        try:
            name = f"{tr.css('td')[2].css("span")[1].text()}"
            ticker = f"{tr.css('td')[2].css("span")[2].text()}"
        except IndexError:
            name = f"{tr.css('td')[2].css("p")[0].text()}"
            ticker = f"{tr.css('td')[2].css("p")[1].text()}"
        price = float(f"{(tr.css('td')[3].text().replace("$", "").replace(",", ""))}")
        if parse_icons_from_file:
            try:
                icon = icons[ticker]
            except:
                icon = ""

        else:
            try:
                icon = tr.css("img.coin-logo")[0].attributes.get("src")
            except:
                icon = ""

        out[ticker] = {
            "ticker": ticker,
            "price": price,
            "name": name,
            "icon": icon,
            "id": i,
        }

    return out


def parse_icons(filepath=config.HTML_PATH):
    with open(filepath) as f:
        html = f.read()

    tree = HTMLParser(html)
    trs = tree.css("tr")[2::]

    out = {}

    logger.info(f"Found {len(trs)} tr's...")

    for tr in trs:
        try:
            ticker = f"{tr.css('td')[2].css("span")[2].text()}"
        except IndexError:
            ticker = f"{tr.css('td')[2].css("p")[1].text()}"
        try:
            icon = tr.css("img.coin-logo")[0].attributes.get("src")
            out[ticker] = icon
        except:
            continue

    return out


def save_values_to_json(data, filepath=config.JSON_PATH):
    logger.info("opening json file...")
    with open(filepath, "w") as f:
        json.dump(data, f)
    logger.info("closing json file...")


def main():
    save_values_to_json(get_values_from_html_to_dict(parse_icons_from_file=True))
    logger.info("Successfully saved data to json file!")


if __name__ == "__main__":
    main()
