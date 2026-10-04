from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


DEFAULT_TIMEOUT = 15


def fetch_webpage(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    response = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/154.0 Safari/537.36"
            )
        },
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for element in soup(
        ["script", "style", "noscript", "nav", "footer", "header", "aside"]
    ):
        element.decompose()

    content = soup.get_text(" ", strip=True)

    return {
        "url": response.url,
        "title": soup.title.get_text(strip=True) if soup.title else "",
        "domain": urlparse(response.url).netloc.lower(),
        "content": content,
        "status_code": response.status_code,
    }
