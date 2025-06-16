import asyncio
import datetime
import logging
import os
import threading
from textwrap import dedent
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
    run_bot,
)
from helpers import LinkPreview, get_link_content_jina, get_link_preview, last_week

app = Flask(__name__)

BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
JINA_TOKEN = os.environ["JINA_TOKEN"]
GEMINI_TOKEN = os.environ["GEMINI_TOKEN"]

gemini_client = genai.Client(api_key=GEMINI_TOKEN)

bot_loop = asyncio.new_event_loop()
bot_thread = threading.Thread(target=run_bot, args=(bot_loop, BOT_TOKEN), daemon=True)
bot_thread.start()

#
# Workflow for endpoints
#   GET  /             - Index
#   GET  /channels     - Get List of Channels
#   POST /links        - Render currently available links
#   GET  /link-preview - Get Link Preview
#   POST /prompt       - Generate prompt from Links
#   POST /gemini       - Generate Newsletter from Gemini
#


@app.route("/")
def index():
    return render_template("index.html", description=CA_DEFAULT_DESCRIPTION)


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
    channel_ids = [int(v) for k, v in request.form.items() if k.startswith("channel-")]
    links = []
    before, after = last_week()
    for channel_id in channel_ids:
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
        links.extend(channel_links)
    return render_template(
        "links.html",
        links=links,
        description=request.form.get("description", CA_DEFAULT_DESCRIPTION),
    )


@app.route("/link-preview", methods=["GET"])
def link_preview():
    url = request.args.get("url")
    index = request.args.get("index")
    preview = get_link_preview(url)
    return render_template("link-preview.html", preview=preview, index=index)


CA_DEFAULT_DESCRIPTION = """
The community archive is a public archive of Twitter/X tweets voluntarily submitted by users.
It seeks to enable normal people to study the dynamics of online social interactions. By
creating a platform for this open data, it helps us to answer the following questions. How do
ideas begin and spread? Who is responsible for the spread of ideas? How can we better protect
ourselves from coroporations and governments which seek to manipulate the collective
consciousness?
"""


@app.route("/prompt", methods=["POST"])
def prompt():
    linkfields = {k: v for k, v in request.form.items() if k.startswith("url")}
    prompt = dedent(
        """
    I will give you a series of XML-formatted information. I will give you
    instructions on what to do with this information at a later point. The
    tags you will see, and their purpose are as follows. `<url>` - this tag
    corresponds to a URL, this tag will always be followed by a corresponding
    `<content>` tag. The `<content>` tag will contain the contents of the
    previous `<url>` tag. After a series of `<url>` and `<content>` tags, you
    will see a `<description>` tag. After the description tag, I will give you
    further instruction on what to do with this information.
    """
    )
    for field, link in linkfields.items():
        prompt += "\n<url>\n"
        prompt += link
        prompt += "\n</url>\n"
        prompt += "\n<contents>\n"
        prompt += get_link_content_jina(link, JINA_TOKEN)
        prompt += "\n</contents>\n"

    prompt += "\n<description>\n"
    prompt += request.form["description"]
    prompt += "\n</description>\n"

    prompt += dedent(
        """
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
    )

    return render_template("prompt-preview.html", prompt=prompt)


@app.route("/gemini", methods=["POST"])
def gemini():
    prompt = request.form["prompt"]
    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro-preview-06-05",
        contents=prompt,
    )
    return render_template("newsletter.html", contents=response.text)
