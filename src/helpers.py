import datetime
from typing import Tuple
from urllib.parse import urlparse

import requests
from dateutil import relativedelta
from requests_html import HTMLSession


def last_week() -> Tuple[datetime.datetime, datetime.datetime]:
    today = datetime.datetime.now()
    start = today - datetime.timedelta((today.weekday() + 1) % 7)
    sat = start + relativedelta.relativedelta(weekday=relativedelta.SA(-1))
    sun = sat + relativedelta.relativedelta(weekday=relativedelta.SU(-1))
    return sat, sun


class LinkPreview:
    def __init__(self, title, description, image, url):
        self.title: str = title
        self.description: str = description
        self.image: str = image
        self.url: str = url


def get_link_preview(url) -> LinkPreview | None:
    session = HTMLSession()
    if urlparse(url).netloc == "x.com":
        prev = LinkPreview(
            "X-Post with no title", "X-Post with no description", "", url
        )
        return prev

    try:
        response = session.get(url)
        # Extract Open Graph metadata or fallback to standard tags
        title = response.html.find(
            'meta[property="og:title"]',
            first=True,
        )
        if title:
            title = title.attrs.get("content")
        else:
            elem = response.html.find(
                "title",
                first=True,
            )
            if not elem:
                title = ""
                print(f"Failed to get element 'title': {url}")
            else:
                title = elem.text

        description = response.html.find(
            'meta[property="og:description"]',
            first=True,
        )
        if description:
            description = description.attrs.get("content")
        else:
            description = ""
            print(f"Failed to get element 'description': {url}")

        image = response.html.find('meta[property="og:image"]', first=True)
        if image:
            image = image.attrs.get("content")
        else:
            image = ""
            print(f"Failed to get element 'image': {url}")

        prev = LinkPreview(title, description, image, url)
        return prev
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None
    finally:
        session.close()


def get_link_content_jina(url: str, token: str) -> str:
    url = f"https://r.jina.ai/{url}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.text
