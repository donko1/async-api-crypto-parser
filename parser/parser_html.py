import json
import os
from selectolax.parser import HTMLParser
from config.settings import config
from core.logger import get_logger

logger = get_logger("parser_html")


def get_price_in_value(elem, value=None):
    """Returns data from elem tr in following pattern:
    [
     {"name":"BTC"
     ....},
     {"name":"ETH",
     ...},
     {
        "name": "USD",
        "price": float,
        "volume24h": float,
        "volume7d": float,
        "volumePercentChange": float,
        "volume30d": float,
        "marketCap": float,
        "percentChange1h": float,
        "percentChange24h": float,
        "percentChange7d": float,
        "lastUpdated": "2000-01-01T12:00:00.000Z",
        "percentChange30d": float,
        "percentChange60d": float,
        "percentChange90d": float,
        "fullyDilluttedMarketCap": float,
        "marketCapByTotalSupply": float,
        "dominance": float,
        "turnover": float,
        "ytdPriceChangePercentage": float2,
        "percentChange1y": float
      }
    ]
    """
    value_convert = {"USD": -1, "ETH": -2, "BTC": -3}

    if value is None:
        value = "USD"

    if value not in value_convert.keys():
        raise Exception("This value doesnt available")

    return elem["quotes"][value_convert[value]]


def find_elem_by_ticker(json_data_all, ticker):
    for elem in json_data_all:
        if elem["symbol"] == ticker:
            return elem


def get_values_from_html_to_dict(
    filepath=config.HTML_PATH,
    parse_icons_from_file=False,
    icons_path=config.ICONS,
    skipping_json_expanded_data=False,
):
    with open(filepath) as f:
        html = f.read()

    tree = HTMLParser(html)
    trs = tree.css("tr")[2::]

    if not skipping_json_expanded_data:
        json_data = json.loads(tree.css_first("script#__NEXT_DATA__").text())["props"][
            "dehydratedState"
        ]["queries"][2]["state"]["data"]["data"]["listing"]["cryptoCurrencyList"]
    else:
        json_data = False

    out = {}

    logger.info(f"Found {len(trs)} tr's...")

    if parse_icons_from_file and os.path.exists(icons_path):
        with open(icons_path) as f:
            icons = json.load(f)

    counter_lost = 0

    for i, tr in enumerate(trs):
        try:
            name = f"{tr.css('td')[2].css("span")[1].text()}"
            ticker = f"{tr.css('td')[2].css("span")[2].text()}"
        except IndexError:
            name = f"{tr.css('td')[2].css("p")[0].text()}"
            ticker = f"{tr.css('td')[2].css("p")[1].text()}"
        if json_data:
            data = get_price_in_value(find_elem_by_ticker(json_data, ticker))
            price = data["price"]
            change_1hr = data["percentChange1h"] / 100
            change_24hr = data["percentChange24h"] / 100
            volume_24hr = data["volume24h"]
        else:
            change_24hr = None
            volume_24hr = None
            price = float(
                f"{(tr.css('td')[3].text().replace("$", "").replace(",", ""))}"
            )
            try:
                change_1hr = (
                    float(tr.css(".icon-Caret-up")[0].parent.text().replace("%", ""))
                    / 100
                )
            except:
                counter_lost += 1
                change_1hr = 0

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

        if not icon and json_data:
            data_full = find_elem_by_ticker(json_data, ticker)
            id = data_full["id"]
            icon = f"https://s2.coinmarketcap.com/static/img/coins/64x64/{id}.png"

        out[ticker] = {
            "ticker": ticker,
            "price": price,
            "name": name,
            "icon": icon,
            "id": i,
            "change_1hr": change_1hr,
            "change_24hr": change_24hr,
            "volume_24hr": volume_24hr,
        }

    if counter_lost > 0:
        logger.info(f"change_1hr was lost {counter_lost}")

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


def lost_icons_count(filepath=config.JSON_PATH):
    logger.info("opening json file...")
    with open(filepath) as f:
        data = json.load(f)
    logger.info("closing json file...")
    count = 0
    for item in data.values():
        if not item["icon"]:
            count += 1
    return count


def main():
    save_values_to_json(get_values_from_html_to_dict(parse_icons_from_file=True))
    logger.info("Successfully saved data to json file!")


if __name__ == "__main__":
    main()
