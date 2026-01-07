import json
from selectolax.parser import HTMLParser
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html_path = os.path.join(base_dir, "html_cache", f"html_cache.html")
json_path = os.path.join(base_dir, "json_cache", f"json_coins.json")


def get_values_from_html_to_dict(filepath=html_path):
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


def save_values_to_json(data, filepath=json_path):
    with open(filepath, "w") as f:
        json.dump(data, f)


def main():
    save_values_to_json(get_values_from_html_to_dict())
    print("Successfully completed!")


if __name__ == "__main__":
    main()
