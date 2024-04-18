from bs4 import BeautifulSoup


def get_text_from_html(html: str) -> str:
    return BeautifulSoup(html, features="html.parser").get_text()
