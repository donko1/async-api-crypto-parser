import json
from selectolax.parser import HTMLParser
import os
from config.settings import config


def get_values_from_html_to_dict(filepath=config.HTML_PATH):
    with open(filepath) as f:
        html = f.read()

    tree = HTMLParser(html)
    trs = tree.css("tr")[2::]

    out = {}

    for i, tr in enumerate(trs):
        try:
            name = f"{tr.css('td')[2].css("span")[1].text()}"
            ticker = f"{tr.css('td')[2].css("span")[2].text()}"
        except IndexError:
            name = f"{tr.css('td')[2].css("p")[0].text()}"
            ticker = f"{tr.css('td')[2].css("p")[1].text()}"
        price = f"{tr.css('td')[3].text().replace("$", "").replace(",", ".")}"

        out[ticker] = {"ticker": ticker, "price": price, "name": name, "id": i}

    return out


def save_values_to_json(data, filepath=config.JSON_PATH):
    with open(filepath, "w") as f:
        json.dump(data, f)


def main():
    save_values_to_json(get_values_from_html_to_dict())
    print("Successfully completed!")


if __name__ == "__main__":
    main()
