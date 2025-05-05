# Discord Newsletter Generator
## How To Run
Firstly, make sure that Docker is [installed and running](https://docs.docker.com/engine/install/).

Then get API keys for the following:
- [Google Gemini](https://ai.google.dev)
- [Jina Ai](https://jina.ai)
- [Your Discord Bot](https://discord.com/developers/docs/intro)

> TODO: add detail here

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
