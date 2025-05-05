from datetime import datetime
import discord
from discord.ext import commands
import re
import asyncio
import logging
from typing import List

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)

# Initialize the bot with required intents
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
bot = commands.Bot(command_prefix='!', intents=intents)

# Regex to match URLs
URL_REGEX = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+'

async def get_channel_name(channel_id: int) -> str:
    try:
        # Ensure the bot is ready
        await bot.wait_until_ready()
        
        # Get the channel object
        channel = bot.get_channel(channel_id)
        if not channel:
            logging.error(f"Channel with ID {channel_id} not found or bot lacks access.")
            return ""

        return channel.name

    except discord.errors.Forbidden:
        logging.error("Bot does not have permission to access the channel.")
        return ""
    except Exception as e:
        logging.error(f"Error getting channel name: {str(e)}")
        return ""

async def get_channels() -> list[discord.TextChannel]:
    try:
        # Ensure the bot is ready
        await bot.wait_until_ready()

        text_channel_list = []
        for guild in bot.guilds:
            for channel in guild.text_channels:
                text_channel_list.append(channel)
        return text_channel_list
    except discord.errors.Forbidden:
        logging.error("Bot does not have permission to view channels.")
        return []
    except Exception as e:
        logging.error(f"Error fetching links: {str(e)}")
        return []
            

async def fetch_links_from_channel(channel_id: int, after: datetime, before: datetime, limit: int = None) -> List[str]:
    """
    Fetches all URLs from a specified channel's message history.
    
    Args:
        channel_id (int): The ID of the Discord channel.
        limit (int, optional): Maximum number of messages to fetch. None for all messages.
    
    Returns:
        List[str]: List of URLs found in the channel.
    """
    try:
        # Ensure the bot is ready
        await bot.wait_until_ready()
        
        # Get the channel object
        channel = bot.get_channel(channel_id)
        if not channel:
            logging.error(f"Channel with ID {channel_id} not found or bot lacks access.")
            return []

        # Check if the bot has permission to read message history
        if not channel.permissions_for(channel.guild.me).read_message_history:
            logging.error(f"Bot lacks 'Read Message History' permission in channel {channel_id}.")
            return []

        links = []
        logging.info(f"Fetching messages from channel: {channel.name} (ID: {channel_id})")

        # Fetch messages asynchronously
        async for message in channel.history(before=before, after=after, limit=limit):
            if message.content:
                # Find all URLs in the message content
                found_links = re.findall(URL_REGEX, message.content)
                links.extend(found_links)

        logging.info(f"Found {len(links)} links in channel {channel.name}")
        return links

    except discord.errors.Forbidden:
        logging.error("Bot does not have permission to access the channel.")
        return []
    except Exception as e:
        logging.error(f"Error fetching links: {str(e)}")
        return []
