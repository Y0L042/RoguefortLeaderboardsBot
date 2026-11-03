"""Print the boards from config.toml to the terminal, without Discord."""

import asyncio
import sys

from config import load_config
from leaderboard import build_embeds
from scores import fetch_scores


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # emoji on Windows consoles
    for dungeon in load_config().dungeons:
        if not dungeon.visible:
            print(f"[hidden] {dungeon.name}\n")
            continue
        for embed in build_embeds(dungeon, await fetch_scores(dungeon)):
            if embed.author.name:
                print(f"== {embed.author.name} ==")
            print(embed.title)
            print(embed.description, end="\n\n")


if __name__ == "__main__":
    asyncio.run(main())
