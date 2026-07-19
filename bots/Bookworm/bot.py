import asyncio
import logging
import os
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from .embeds import build_book_embed
from .hardcover import HardcoverAPIError, get_book, search_books


load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Only these channels may use the bot.
ALLOWED_CHANNEL_IDS = {
    1528131875921465395,
    1525518537232220170,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


def _is_allowed_channel(
    interaction: discord.Interaction,
) -> bool:
    """Return whether the interaction came from an approved channel."""

    return (
        interaction.channel_id is not None
        and interaction.channel_id in ALLOWED_CHANNEL_IDS
    )


class BookBot(commands.Bot):
    """Discord bot providing Hardcover book recommendations."""

    def __init__(self) -> None:
        intents = discord.Intents.default()

        super().__init__(
            command_prefix="!",
            intents=intents,
        )

    async def setup_hook(self) -> None:
        """Synchronise global slash commands."""

        synced = await self.tree.sync()

        logger.info(
            "Synced %s global command(s).",
            len(synced),
        )

    async def on_ready(self) -> None:
        """Log when the bot connects to Discord."""

        if self.user is None:
            return

        logger.info(
            "Logged in as %s (%s)",
            self.user,
            self.user.id,
        )


bot = BookBot()


def create_bot() -> BookBot:
    """Return the configured, unstarted Bookworm Discord bot."""

    return bot


def _autocomplete_name(book: dict[str, Any]) -> str:
    """Build a readable autocomplete label."""

    title = str(
        book.get("title") or "Unknown title"
    ).strip()

    authors = book.get("authors") or []

    if isinstance(authors, list) and authors:
        author_text = ", ".join(
            str(author).strip()
            for author in authors[:2]
            if str(author).strip()
        )

        label = f"{title} — {author_text}"
    else:
        label = title

    if len(label) > 100:
        label = label[:97].rstrip() + "..."

    return label


async def book_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Search Hardcover while the user types."""

    if not _is_allowed_channel(interaction):
        return []

    search_term = current.strip()

    if len(search_term) < 2:
        return []

    try:
        books = await asyncio.to_thread(
            search_books,
            search_term,
            limit=10,
        )

    except HardcoverAPIError as error:
        logger.warning(
            "Hardcover autocomplete failed: %s",
            error,
        )
        return []

    except Exception:
        logger.exception(
            "Unexpected autocomplete error."
        )
        return []

    choices: list[app_commands.Choice[str]] = []

    for book in books:
        book_id = book.get("id")

        if book_id is None:
            continue

        choices.append(
            app_commands.Choice(
                name=_autocomplete_name(book),
                value=str(book_id),
            )
        )

    return choices


@bot.tree.command(
    name="recommend_book",
    description="Find information about a book on Hardcover.",
)
@app_commands.describe(
    book="Start typing a book title or author.",
)
@app_commands.autocomplete(
    book=book_autocomplete,
)
async def recommend_book(
    interaction: discord.Interaction,
    book: str,
) -> None:
    """Retrieve and display the selected book."""

    if not _is_allowed_channel(interaction):
        await interaction.response.send_message(
            "This command cannot be used in this channel.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(
        thinking=True,
    )

    try:
        book_id = int(book)

    except ValueError:
        await interaction.followup.send(
            (
                "Please select a book from the "
                "autocomplete suggestions."
            ),
            ephemeral=True,
        )
        return

    try:
        book_data = await asyncio.to_thread(
            get_book,
            book_id,
        )

    except HardcoverAPIError as error:
        logger.warning(
            "Hardcover lookup failed for book %s: %s",
            book_id,
            error,
        )

        await interaction.followup.send(
            (
                "I couldn't retrieve that book from Hardcover "
                "right now. Please try again shortly."
            ),
            ephemeral=True,
        )
        return

    except Exception:
        logger.exception(
            "Unexpected error retrieving book %s.",
            book_id,
        )

        await interaction.followup.send(
            "Something unexpected went wrong.",
            ephemeral=True,
        )
        return

    if book_data is None:
        await interaction.followup.send(
            "That book could not be found on Hardcover.",
            ephemeral=True,
        )
        return

    embed = build_book_embed(book_data)

    await interaction.followup.send(
        embed=embed,
    )


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
) -> None:
    """Handle uncaught slash-command errors."""

    logger.error(
        "Application command error: %s",
        error,
        exc_info=error,
    )

    message = (
        "The command encountered an unexpected error. "
        "Please try again."
    )

    if interaction.response.is_done():
        await interaction.followup.send(
            message,
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            message,
            ephemeral=True,
        )


def main() -> None:
    """Start the Discord bot."""

    if not DISCORD_TOKEN:
        raise RuntimeError(
            "DISCORD_TOKEN is missing from the .env file."
        )

    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
