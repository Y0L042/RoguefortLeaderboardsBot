"""Discord bot that keeps a single, live-updating leaderboard message in a channel."""

import logging
import os

import discord
from discord.ext import tasks
from dotenv import load_dotenv

from leaderboard import build_embeds
from scores import fetch_scores

log = logging.getLogger(__name__)
client = discord.Client(intents=discord.Intents.default())
CHANNEL_ID: int = 0  # set in main()
message_id: int | None = None  # recovered from channel history on startup


async def get_channel() -> discord.TextChannel:
    channel = client.get_channel(CHANNEL_ID) or await client.fetch_channel(CHANNEL_ID)
    assert isinstance(channel, discord.TextChannel), "CHANNEL_ID must be a text channel"
    return channel

@tasks.loop(seconds=60)
async def refresh() -> None:
    """Edit the leaderboard message, or post a new one if it doesn't exist."""
    global message_id
    try:
        scores = await fetch_scores()
    except Exception:
        # Keep the old board and try again next tick
        log.exception("Failed to fetch scores")
        return
    channel = await get_channel()
    embeds = build_embeds(scores)
    if message_id:
        try:
            msg = await channel.fetch_message(message_id)
            await msg.edit(embeds=embeds)
            return
        except discord.NotFound:
            pass
    msg = await channel.send(embeds=embeds)
    message_id = msg.id

@client.event
async def on_ready() -> None:
    global message_id
    if not refresh.is_running():
        # Reuse the bot's first message in the channel from before a restart
        channel = await get_channel()
        async for msg in channel.history(limit=None, oldest_first=True):
            if msg.author == client.user:
                message_id = msg.id
                break
        refresh.start()

def main() -> None:
    global CHANNEL_ID
    load_dotenv()
    CHANNEL_ID = int(os.environ["CHANNEL_ID"])
    client.run(os.environ["DISCORD_BOT"])

if __name__ == "__main__":
    main()
