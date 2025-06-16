# Discord Newsletter Generator
This is a website which will generate a newsletter based on the links sent in a Discord server.

## Workflow Example Demo
> Note: This demo has been edited for brevity and clarity.

[demo.webm](https://github.com/user-attachments/assets/52d4e11b-4f76-4883-8acf-ccb06d90915e)

[Resulting HTML](/assets/example.html)

## Background
### The Problem
I'm a part of a Discord server for the [Community Archive](https://www.community-archive.org).
The Community Archive is a project to archive X (formerly Twitter) posts. This project's wider goal
is to study the creation and spread of ideas. They've dubbed their work "memetics". Companies like
Palantir and social media companies already study these social dynamics, but they are closed to the
public. In other words, they can study us, but we cannot study ourselves. This is important because
we can figure out how powerful organizations are attempting to manipulate the public consciousness.

This community is growing, and as a result, there's never a dull moment in the server. I'm often
unable to keep up with the latest in the community. Additionally, there's a lot of work to be
done to spread awareness of the problem space. I'm not willing to scan through the server and all
that's going on, but I would surely read a newsletter. This would be a great way to grow the
community. I'm sure there are many who would also be interested in a newsletter.

### The Solution
1. Set up a bot that reads all of the messages in the Discord server from the past week.
2. Present a user with all of the links in the UI. Allow the user to remove any that don't fit the
message.
3. Scrape the contents of the links.
4. Compile the contents of the selected links and a description of the server. Build an LLM prompt
that makes this info available.
5. Pass the built prompt into an LLM with a large context length.

## How To Run
First, make sure that Docker is [installed and running](https://docs.docker.com/engine/install/).

Then get API keys for the following:
- [Google Gemini](https://ai.google.dev)
- [Jina Ai](https://jina.ai)
- [Your Discord Bot](https://discord.com/developers/docs/intro)

Make sure your Discord bot can read the messages of the server it will be connected to.

Then, run the following:
```bash
git clone https://github.com/emmettmcdow/discord-newsletter-generator.git
cd discord-newsletter-generator
export DISCORD_BOT_TOKEN=...
export JINA_TOKEN=...
export GEMINI_TOKEN=...
./run.sh
```
This will start the tool running on port `8080`. Navigate to `http://localhost:8080` in your
browser to start using it.

## Known Issues
- Inconsistent link previewing. Not all websites use opengraph (e.g. x.com).
- Inconsistent web scraping. Currently it uses the [Jina AI API](https://jina.ai). It works well
enough but costs money. There are free options available but would require a significant amount of
development effort. [Playwright](https://playwright.dev) would be a viable option.
- The output format from the LLM is non-deterministic. Meaning if you tell it to produce a
"newsletter similar to Morning Brew" it could give you different formats each time. The prompt
could theoretically be set up to take an HTML template for the newsletter. That way, the format
will not be different from one generation to another.
