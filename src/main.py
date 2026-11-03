import os

import discord
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv()
CHANNEL_ID = int(os.environ["CHANNEL_ID"])
DISCORD_TOKEN = os.environ["DISCORD_BOT"]
client = discord.Client(intents=discord.Intents.default())
message_id = None  # recovered from channel history on startup, so this doesn't need persisting

x = 7
def fetch_scores():
    # Replace with a DB query or API call
    # Rows: (name, level, danger_level, steps, kills, time_seconds), in any order
    global x
    x = x + 1
    return [
        ("Merlinus", 12, 5, 4521, 87, 754 + x),
        ("xXFireballXx", 11, 5, 4210, 79, 790 + x * 2),
        ("Zaltharion", 10, 4, 3980, 64, 812 + x * 10),
        ("PotionSeller", 9, 4, 3310, 51, 905 + x * 100),
        ("Grimbeard", 8, 3, 2875, 42, 1010 + x * 5),
        ("Hexorcist", 8, 3, 2640, 38, 1102),
        ("Gandalfo", 7, 3, 2390, 33, 1187),
        ("ManaPotato", 6, 2, 2015, 27, 1240),
        ("Rincewand", 5, 2, 1780, 19, 1325),
        ("NoobSlayer99", 4, 1, 1320, 12, 1410),
    ]

MEDALS = ["🥇", "🥈", "🥉"]
RANK_EMOJI = ["4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━"

def format_time(total_seconds: int) -> str:
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02}"

def build_embed():
    rows = sorted(fetch_scores(), key=lambda row: row[3])[:10]  # fewest steps first
    lines: list[str] = []
    for i, (name, level, danger, steps, kills, seconds) in enumerate(rows):
        name = discord.utils.escape_markdown(name)
        stats = f"⭐ {level} · ☠️ {danger} · 👣 {steps:,} · ⚔️ {kills} · ⏱️ {format_time(seconds)}"
        if i < 3:
            # Podium: medal, bold name, stats quoted underneath
            lines.append(f"{MEDALS[i]} **{name}**\n> {stats}")
        else:
            if i == 3:
                lines.append(DIVIDER)
            lines.append(f"{RANK_EMOJI[i - 3]} **{name}** — {stats}")

    embed = discord.Embed(
        title="🏆 Roguefort Hall of Fame 🏆",
        description=f"*The bravest adventurers to delve the depths*\n{DIVIDER}\n" + "\n".join(lines),
        colour=0xF1C40F,
    )
    embed.set_footer(text="⭐ Level · ☠️ Danger · 👣 Steps · ⚔️ Kills · ⏱️ Time  •  Updated")
    embed.timestamp = discord.utils.utcnow()
    return embed

async def get_channel() -> discord.TextChannel:
    channel = client.get_channel(CHANNEL_ID) or await client.fetch_channel(CHANNEL_ID)
    assert isinstance(channel, discord.TextChannel), "CHANNEL_ID must be a text channel"
    return channel

@tasks.loop(seconds=60)
async def refresh():
    global message_id
    channel = await get_channel()
    embed = build_embed()
    if message_id:
        try:
            msg = await channel.fetch_message(message_id)
            await msg.edit(embed=embed)
            return
        except discord.NotFound:
            pass  # message was deleted; post a new one
    msg = await channel.send(embed=embed)
    message_id = msg.id

@client.event
async def on_ready():
    if not refresh.is_running():
        # Reuse the bot's first message in the channel from before a restart
        global message_id
        channel = await get_channel()
        async for msg in channel.history(limit=None, oldest_first=True):
            if msg.author == client.user:
                message_id = msg.id
                break
        refresh.start()

client.run(DISCORD_TOKEN)