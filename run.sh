#!/bin/bash

docker build -t discord-nl-gen .
docker run --rm \
           -e DISCORD_BOT_TOKEN -e JINA_TOKEN -e GEMINI_TOKEN \
           -p 8080:8080 \
           discord-nl-gen
