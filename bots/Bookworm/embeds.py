from typing import Any

import discord


MAX_DESCRIPTION_LENGTH = 1_200
MAX_TAGS = 5


def _truncate(text: str, limit: int) -> str:
    """Trim text to a safe Discord embed length."""

    text = text.strip()

    if len(text) <= limit:
        return text

    return text[: limit - 3].rstrip() + "..."


def _format_authors(authors: Any) -> str:
    """Return a readable author string."""

    if not isinstance(authors, list):
        return ""

    valid_authors = [
        str(author).strip()
        for author in authors
        if str(author).strip()
    ]

    return ", ".join(valid_authors)


def _format_rating(
    rating: Any,
    ratings_count: Any,
) -> str:
    """Format the rating and ratings count."""

    if rating is None:
        return ""

    try:
        rating_text = f"{float(rating):.2f} / 5"
    except (TypeError, ValueError):
        rating_text = str(rating)

    try:
        count = int(ratings_count or 0)
    except (TypeError, ValueError):
        count = 0

    if count:
        rating_text += f" ({count:,} ratings)"

    return rating_text


def _format_tags(tags: Any) -> str:
    """Format a limited number of genres or moods."""

    if not isinstance(tags, list):
        return ""

    valid_tags = [
        str(tag).strip()
        for tag in tags
        if str(tag).strip()
    ]

    return " • ".join(valid_tags[:MAX_TAGS])


def build_book_embed(
    book: dict[str, Any],
    suggested_by: str | None = None,
) -> discord.Embed:
    """Build a Discord embed from a normalised Hardcover book record."""

    title = str(
        book.get("title")
        or "Unknown title"
    ).strip()

    subtitle = str(
        book.get("subtitle")
        or ""
    ).strip()

    description = str(
        book.get("description")
        or ""
    ).strip()

    hardcover_url = book.get("hardcover_url")

    embed_title = title

    if subtitle:
        embed_title = f"{title}: {subtitle}"

    embed = discord.Embed(
        title=_truncate(embed_title, 256),
        url=hardcover_url if hardcover_url else None,
        colour=discord.Colour.blurple(),
    )

    authors = _format_authors(
        book.get("authors")
    )

    if authors:
        embed.set_author(
            name=authors,
        )

    if description:
        embed.description = _truncate(
            description,
            MAX_DESCRIPTION_LENGTH,
        )

    rating = _format_rating(
        book.get("rating"),
        book.get("ratings_count"),
    )

    if rating:
        embed.add_field(
            name="⭐ Rating",
            value=rating,
            inline=True,
        )

    reviews_count = book.get("reviews_count")

    try:
        reviews_count = int(reviews_count or 0)
    except (TypeError, ValueError):
        reviews_count = 0

    if reviews_count:
        embed.add_field(
            name="💬 Reviews",
            value=f"{reviews_count:,}",
            inline=True,
        )

    release_date = book.get("release_date")
    release_year = book.get("release_year")

    release_value = release_date or release_year

    if release_value:
        embed.add_field(
            name="📅 Released",
            value=str(release_value),
            inline=True,
        )

    pages = book.get("pages")

    try:
        pages = int(pages) if pages else None
    except (TypeError, ValueError):
        pages = None

    if pages:
        embed.add_field(
            name="📖 Pages",
            value=f"{pages:,}",
            inline=True,
        )

    genres = _format_tags(
        book.get("genres")
    )

    if genres:
        embed.add_field(
            name="🏷️ Genres",
            value=genres,
            inline=False,
        )

    moods = _format_tags(
        book.get("moods")
    )

    if moods:
        embed.add_field(
            name="🎭 Moods",
            value=moods,
            inline=False,
        )

    cover_url = book.get("cover_url")

    if cover_url:
        embed.set_thumbnail(
            url=str(cover_url),
        )

    if hardcover_url:
        embed.add_field(
            name="🔗 Hardcover",
            value=f"[View book on Hardcover]({hardcover_url})",
            inline=False,
        )

    if suggested_by:
        embed.add_field(
            name="Suggested by",
            value=suggested_by,
            inline=False,
        )

    embed.set_footer(
        text="Book data provided by Hardcover",
    )

    return embed
