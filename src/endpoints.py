import asyncio
import datetime
import logging
import os
import threading
from typing import Tuple
from urllib.parse import urlparse

import requests
from dateutil import relativedelta
from flask import Flask, render_template, request
from google import genai
from requests_html import HTMLSession  # type: ignore

from discord_bot import (
    bot,
    fetch_links_from_channel,
    get_channel_name,
    get_channels,
)

app = Flask(__name__)

BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
JINA_TOKEN = os.environ["JINA_TOKEN"]
GEMINI_TOKEN = os.environ["GEMINI_TOKEN"]

gemini_client = genai.Client(api_key=GEMINI_TOKEN)

bot_loop = asyncio.new_event_loop()


def run_bot():
    """
    Runs the Discord bot in a separate thread with its own event loop.
    """
    asyncio.set_event_loop(bot_loop)
    try:
        print(BOT_TOKEN)
        bot_loop.run_until_complete(bot.start(BOT_TOKEN))
    except Exception as e:
        logging.error(f"Bot error: {str(e)}")
    finally:
        bot_loop.run_until_complete(bot.close())
        bot_loop.close()


bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()


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


def get_link_content_jina(url: str) -> str:
    url = f"https://r.jina.ai/{url}"
    headers = {"Authorization": f"Bearer {JINA_TOKEN}"}
    response = requests.get(url, headers=headers)
    return response.text


@app.route("/")
def hello_world():
    return render_template("index.html")


@app.route("/channels", methods=["GET"])
def channels():
    future_channels = asyncio.run_coroutine_threadsafe(
        get_channels(),
        bot_loop,
    )
    channels = future_channels.result(timeout=60)

    return render_template("channels.html", channels=channels)


@app.route("/links", methods=["POST"])
def links():
    prompt = """
    I will give you a series of XML-formatted information. I will give you
    instructions on what to do with this information at a later point. The
    tags you will see, and their purpose are as follows. `<url>` - this tag
    corresponds to a URL, this tag will always be followed by a corresponding
    `<content>` tag. The `<content>` tag will contain the contents of the
    previous `<url>` tag. After a series of `<url>` and `<content>` tags, you
    will see a `<description>` tag. After the description tag, I will give you
    further instruction on what to do with this information.
    """
    for field, link in request.form.items():
        if not field.startswith("url"):
            continue
        prompt += "\n<url>\n"
        prompt += link
        prompt += "\n</url>\n"
        prompt += "\n<contents>\n"
        prompt += get_link_content_jina(link)
        prompt += "\n</contents>\n"

    prompt += "\n<description>\n"
    prompt += request.form["description"]
    prompt += "\n</description>\n"

    prompt += """
    I want you to produce a newsletter.

    The topic of the newsletter is described in the `<description>` tag above.

    Start the newsletter with a 3-5 sentence summary of all of the
    links I gave to you above. After that for each link mentioned above
    (`<url>` and `<content>` combos), give a short description of each link
    and how it relates to the mission of the `<description>`.

    Be brief, only use 1-2 sentences per link.

    Write the newsletter in the style of Morning Brew. It is a weekly
    newsletter.

    I want you to output HTML and only HTML. Do not talk to me.
    """

    return render_template("preview.html", prompt=prompt)


@app.route("/gemini", methods=["POST"])
def gemini():
    prompt = request.form["prompt"]
    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro-exp-03-25",
        contents=prompt,
    )
    return render_template("newsletter.html", contents=response.text)


@app.route("/links/<channel_id>", methods=["GET"])
def links_for_channel(channel_id: int):
    channel_id = int(channel_id)
    before, after = last_week()
    future_name = asyncio.run_coroutine_threadsafe(
        get_channel_name(channel_id), bot_loop
    )
    channel_name = future_name.result(timeout=60)

    future_links = asyncio.run_coroutine_threadsafe(
        fetch_links_from_channel(
            channel_id,
            limit=100,
            before=before,
            after=after,
        ),
        bot_loop,
    )
    channel_links = future_links.result(timeout=60)

    previews = [get_link_preview(url) for url in channel_links if url]

    return render_template(
        "links.html",
        channel_name=channel_name,
        previews=previews,
    )
