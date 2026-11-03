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

The bot posts the leaderboard on startup and refreshes it every 60 seconds. The message holds two boards:

- **Swiftest**: wins first, then fewest turns.
- **Mastery**: highest mastery score first.

Scores come from the source named by the optional `SCORE_SOURCE` variable (default `mock`, fake data). To add a real source, write a class with an async `fetch()` in `src/scores.py` and register it in `SOURCES`.

## Tests

```sh
uv run pytest
```

## Troubleshooting

| Error                          | Cause                                                               |
| ------------------------------ | ------------------------------------------------------------------- |
| `403 Forbidden (50001)`        | Bot is not in the server, or cannot view the channel. Recheck steps 2 and 3. |
| `404 Not Found` on the channel | Wrong `CHANNEL_ID`, or the ID belongs to a different server.        |
| `LoginFailure`                 | Invalid token. Reset it and update `.env`.                          |