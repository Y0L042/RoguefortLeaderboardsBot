"""Discord bot that keeps one live-updating leaderboard message per dungeon in a channel."""

import logging
import os

import discord
from discord.ext import tasks
from dotenv import load_dotenv

from config import DEFAULT_REFRESH_SECONDS, Config, Dungeon, load_config
from leaderboard import build_embeds, dungeon_label
from scores import fetch_scores

log = logging.getLogger(__name__)
client = discord.Client(intents=discord.Intents.default())
CHANNEL_ID: int = 0  # set in main()
config = Config(DEFAULT_REFRESH_SECONDS, [])  # last valid config
message_ids: dict[str, int] = {}  # dungeon id -> message id, recovered on startup
stale_ids: list[int] = []  # bot messages that belong to no dungeon, deleted on refresh


def reload_config() -> None:
    """Reload config.toml, keeping the last valid config if it is broken."""
    global config
    try:
        config = load_config()
    except (OSError, ValueError):  # includes ConfigError and TOML syntax errors
        log.exception("Failed to load config.toml, keeping the previous config")
        return
    if refresh.seconds != config.refresh_seconds:
        # Takes effect from the next iteration
        refresh.change_interval(seconds=config.refresh_seconds)

async def get_channel() -> discord.TextChannel:
    channel = client.get_channel(CHANNEL_ID) or await client.fetch_channel(CHANNEL_ID)
    assert isinstance(channel, discord.TextChannel), "CHANNEL_ID must be a text channel"
    return channel

async def delete_message(channel: discord.TextChannel, msg_id: int) -> None:
    try:
        await channel.get_partial_message(msg_id).delete()
    except discord.NotFound:
        pass

async def update_dungeon(channel: discord.TextChannel, dungeon: Dungeon) -> None:
    """Edit the dungeon's message, or post a new one if it doesn't exist."""
    embeds = build_embeds(dungeon, await fetch_scores(dungeon))
    if dungeon.id in message_ids:
        try:
            msg = await channel.fetch_message(message_ids[dungeon.id])
            await msg.edit(embeds=embeds)
            return
        except discord.NotFound:
            pass
    msg = await channel.send(embeds=embeds)
    message_ids[dungeon.id] = msg.id

@tasks.loop(seconds=DEFAULT_REFRESH_SECONDS)
async def refresh() -> None:
    reload_config()
    channel = await get_channel()
    while stale_ids:
        await delete_message(channel, stale_ids.pop())
    for dungeon in config.dungeons:
        if not dungeon.visible:
            if dungeon.id in message_ids:
                await delete_message(channel, message_ids.pop(dungeon.id))
            continue
        try:
            await update_dungeon(channel, dungeon)
        except Exception:
            # Keep the old board and try again next tick
            log.exception("Failed to update %s", dungeon.id)
    # Messages of dungeons removed from the config entirely
    known = {dungeon.id for dungeon in config.dungeons}
    for dungeon_id in [d for d in message_ids if d not in known]:
        await delete_message(channel, message_ids.pop(dungeon_id))

@client.event
async def on_ready() -> None:
    if not refresh.is_running():
        # Reuse the bot's messages from before a restart, matched by dungeon label
        reload_config()
        labels = {dungeon_label(dungeon): dungeon.id for dungeon in config.dungeons}
        channel = await get_channel()
        async for msg in channel.history(limit=None, oldest_first=True):
            if msg.author != client.user:
                continue
            author = msg.embeds[0].author.name if msg.embeds else None
            dungeon_id = labels.get(author or "")
            if dungeon_id and dungeon_id not in message_ids:
                message_ids[dungeon_id] = msg.id
            else:
                stale_ids.append(msg.id)
        refresh.start()

def main() -> None:
    global CHANNEL_ID
    load_dotenv()
    CHANNEL_ID = int(os.environ["CHANNEL_ID"])
    client.run(os.environ["DISCORD_BOT"])

if __name__ == "__main__":
    main()
