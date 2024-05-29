from bs4 import BeautifulSoup


def get_text_from_html(html: str) -> str:
    if html:
        return BeautifulSoup(html, features="html.parser").get_text()
    else:
        return ""
