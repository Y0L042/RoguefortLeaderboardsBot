# Roguefort Leaderboards Bot

A Discord bot that posts a leaderboard embed in a read-only channel (`#Leaderboard`) and edits that same message on a timer, so the board stays current without new posts.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- A Discord server where you have the **Manage Server** permission

## 1. Create the bot

1. Open the [Discord Developer Portal](https://discord.com/developers/applications) and create a **New Application**.
2. Go to **Bot**, then **Reset Token** and copy the token.

## 2. Invite the bot to your server

1. In the Developer Portal, go to **OAuth2 → URL Generator**.
2. Under **Scopes**, tick `bot`.
3. Under **Bot Permissions**, tick:
   - View Channels
   - Send Messages
   - Embed Links
   - Read Message History
4. Open the generated URL in a browser, choose your server, and authorize.

## 3. Set up the channel

1. Create a channel named `#Leaderboard`.
2. Open **Edit Channel → Permissions**:
   - `@everyone`: deny **Send Messages**.
   - The bot (or its role): allow **View Channel**, **Send Messages**, **Embed Links** and **Read Message History**.

The bot's override takes precedence over the `@everyone` deny, so users can read but not post.

## 4. Get the channel ID

1. Enable **User Settings → Advanced → Developer Mode**.
2. Right-click `#Leaderboard` and choose **Copy Channel ID**.

## 5. Configure `.env`

Create a `.env` file in the project root:

```dotenv
DISCORD_BOT=your-bot-token-here
CHANNEL_ID=123456789012345678
```

| Variable      | Description                                      |
| ------------- | ------------------------------------------------ |
| `DISCORD_BOT` | Bot token from the Developer Portal              |
| `CHANNEL_ID`  | ID of the `#Leaderboard` channel                 |

Do not commit `.env`. Add it to `.gitignore`:

```gitignore
.env
```

Treat the token like a password. If it leaks, reset it in the Developer Portal.

## 6. Run

```sh
uv run src/main.py
```

The bot posts one message per dungeon on startup and refreshes them every `refresh_seconds` (default 60, set in `config.toml`). Each message holds that dungeon's boards:

- **Swiftest**: wins first, then fewest turns.
- **Mastery**: highest mastery score first.

## 7. Configure dungeons and boards

The refresh interval, dungeons and their boards are set in `config.toml`. The bot reloads this file on every refresh, so you do not need to restart it after a change. If the file is invalid, the bot logs the error and keeps the last valid config.

```toml
refresh_seconds = 60  # minimum 10

[dungeons.monadic]
name = "The Monadic Descent"
players = 1
enabled = true
boards = { swiftest = true, mastery = true }
```

- **Change the refresh interval:** set `refresh_seconds`. It takes effect after the next refresh.
- **Hide a board:** set it to `false`, for example `mastery = false`.
- **Hide a dungeon:** set `enabled = false`. The bot deletes its message.
- **Add a dungeon:** add a new `[dungeons.<id>]` block.
- **Add a board type:** add a `BoardType` (columns and ranking) to `BOARD_TYPES` in `src/leaderboard.py`, then name it in `config.toml`.

Messages are posted in config order. A dungeon that you enable later is posted at the bottom of the channel.

> The bot matches its messages to dungeons by the label above the first board (for example "The Monadic Descent · 1 player"). It deletes any of its own messages in the channel that do not match a visible dungeon.

Scores come from the source named by the optional `SCORE_SOURCE` variable (default `mock`, fake data). To add a real source, write a class with an async `fetch()` in `src/scores.py` and register it in `SOURCES`.

## Make targets

Run `make` to list them:

| Target         | Description                                                       |
| -------------- | ----------------------------------------------------------------- |
| `make install` | Install dependencies, including test tools                       |
| `make run`     | Start the bot                                                     |
| `make test`    | Run the tests                                                     |
| `make preview` | Print the boards from `config.toml` with mock data, without Discord |
| `make clean`   | Remove caches                                                     |

## Troubleshooting

| Error                          | Cause                                                               |
| ------------------------------ | ------------------------------------------------------------------- |
| `403 Forbidden (50001)`        | Bot is not in the server, or cannot view the channel. Recheck steps 2 and 3. |
| `404 Not Found` on the channel | Wrong `CHANNEL_ID`, or the ID belongs to a different server.        |
| `LoginFailure`                 | Invalid token. Reset it and update `.env`.                          |

## Project layout

| File                  | Description                                                                                      |
| --------------------- | ------------------------------------------------------------------------------------------------ |
| `src/main.py`         | The Discord bot. Every `refresh_seconds` it posts or edits one message per dungeon, finds its messages again after a restart, and deletes messages it no longer needs. |
| `src/leaderboard.py`  | The `Score` record, board types (`BOARD_TYPES`), and rendering of the tables and embeds. No Discord connection or env vars. |
| `src/config.py`       | Loads and validates `config.toml` into a `Config` (refresh interval and `Dungeon`s).                                     |
| `src/scores.py`       | Where scores come from: the `ScoreSource` interface, `parse_score()`, and the mock source.       |
| `src/preview.py`      | Prints the boards to the terminal without Discord (`make preview`).                             |
| `config.toml`         | Refresh interval, and which dungeons and boards are shown. Reloaded on every refresh.                                |
| `tests/`              | Tests for the config, rendering and score sources (`make test`).                                 |
| `Makefile`            | Shortcuts for installing, running, testing and previewing.                                       |