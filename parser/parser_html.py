from selectolax.parser import HTMLParser
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(base_dir, "html_cache", f"html_cache.html")


def get_values_from_html_to_dict(filepath=file_path):
    with open(file_path) as f:
        html = f.read()

    tree = HTMLParser(html)
    trs = tree.css("tr")[2::]
    for tr in trs:
        try:
            print(f"{tr.css('td')[2].css("span")[1].text()}")
            print(f"{tr.css('td')[2].css("span")[2].text()}")
        except IndexError:
            print(f"{tr.css('td')[2].css("p")[0].text()}")
            print(f"{tr.css('td')[2].css("p")[1].text()}")
        print(f"{tr.css('td')[3].text().replace("$", "").replace(",", ".")}\n")


def main():
    print(get_values_from_html_to_dict())


if __name__ == "__main__":
    main()
