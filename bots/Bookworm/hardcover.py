import os
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv()

API_URL = "https://api.hardcover.app/v1/graphql"
TOKEN = os.getenv("HARDCOVER_API_TOKEN")


class HardcoverAPIError(Exception):
    """Raised when the Hardcover API request fails."""


def _graphql_request(
    query: str,
    variables: dict[str, Any],
) -> dict[str, Any]:
    """Send a GraphQL request to Hardcover."""

    if not TOKEN:
        raise HardcoverAPIError(
            "HARDCOVER_API_TOKEN is missing from .env"
        )

    try:
        response = requests.post(
            API_URL,
            headers={
                "authorization": f"Bearer {TOKEN}",
                "content-type": "application/json",
            },
            json={
                "query": query,
                "variables": variables,
            },
            timeout=20,
        )

        # Handle rate limiting explicitly
        if response.status_code == 429:
            raise HardcoverAPIError(
            "Hardcover API rate limit exceeded. Please try again later.")

        response.raise_for_status()

    except requests.RequestException as error:
        raise HardcoverAPIError(
            f"Hardcover request failed: {error}"
        ) from error

    try:
        payload = response.json()
    except requests.JSONDecodeError as error:
        raise HardcoverAPIError(
            "Hardcover returned invalid JSON."
        ) from error

    if payload.get("errors"):
        messages = [
            item.get("message", "Unknown GraphQL error")
            for item in payload["errors"]
        ]

        raise HardcoverAPIError("; ".join(messages))

    data = payload.get("data")

    if not isinstance(data, dict):
        raise HardcoverAPIError(
            "Hardcover returned an unexpected response."
        )

    return data


def _rank_book(hit: dict[str, Any]) -> tuple[int, int]:
    """Push summaries and study guides below original books."""

    book = hit.get("document", {})
    title = (book.get("title") or "").lower()
    ratings_count = book.get("ratings_count") or 0

    unwanted_words = (
        "summary",
        "analysis",
        "review",
        "key takeaways",
        "study guide",
    )

    is_unwanted = any(
        word in title
        for word in unwanted_words
    )

    return (
        0 if is_unwanted else 1,
        ratings_count,
    )


def _extract_tag_names(
    cached_tags: Any,
    category: str,
) -> list[str]:
    """Extract tag names from Hardcover cached tag data."""

    if not isinstance(cached_tags, dict):
        return []

    values = cached_tags.get(category)

    if not isinstance(values, list):
        return []

    names: list[str] = []

    for item in values:
        if not isinstance(item, dict):
            continue

        name = item.get("tag")

        if name:
            names.append(str(name))

    return list(dict.fromkeys(names))


def _extract_authors(
    cached_contributors: Any,
) -> list[str]:
    """Extract author names from cached contributor data."""

    if not cached_contributors:
        return []

    contributors = cached_contributors

    if isinstance(contributors, dict):
        contributors = (
            contributors.get("contributions")
            or contributors.get("authors")
            or contributors.get("items")
            or []
        )

    if not isinstance(contributors, list):
        return []

    ignored_roles = {
        "translator",
        "illustrator",
        "editor",
        "narrator",
        "foreword",
    }

    authors: list[str] = []

    for contributor in contributors:
        if isinstance(contributor, str):
            authors.append(contributor)
            continue

        if not isinstance(contributor, dict):
            continue

        author = contributor.get("author")

        if isinstance(author, dict):
            name = author.get("name")
        else:
            name = (
                contributor.get("name")
                or contributor.get("author_name")
            )

        role = (
            contributor.get("contribution")
            or contributor.get("type")
            or ""
        )

        if (
            name
            and str(role).lower() not in ignored_roles
        ):
            authors.append(str(name))

    return list(dict.fromkeys(authors))


def search_books(
    search_term: str,
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search Hardcover and return ranked autocomplete results."""

    query = """
    query SearchBooks($query: String!) {
      search(
        query: $query
        query_type: "Book"
        per_page: 20
      ) {
        results
      }
    }
    """

    data = _graphql_request(
        query,
        {"query": search_term},
    )

    try:
        hits = data["search"]["results"]["hits"]
    except (KeyError, TypeError):
        return []

    if not isinstance(hits, list):
        return []

    hits.sort(
        key=_rank_book,
        reverse=True,
    )

    books: list[dict[str, Any]] = []

    for hit in hits[:limit]:
        document = hit.get("document", {})

        book_id = document.get("id")
        title = document.get("title")

        if book_id is None or not title:
            continue

        authors = document.get("author_names") or []

        books.append(
            {
                "id": int(book_id),
                "title": str(title),
                "authors": [
                    str(author)
                    for author in authors
                ],
                "rating": document.get("rating"),
                "ratings_count": (
                    document.get("ratings_count") or 0
                ),
                "release_year": document.get("release_year"),
                "slug": document.get("slug"),
            }
        )

    return books


def get_book(book_id: int) -> dict[str, Any] | None:
    """Retrieve a complete Hardcover book record by ID."""

    query = """
    query GetBook($id: Int!) {
      books_by_pk(id: $id) {
        id
        title
        subtitle
        description
        slug

        rating
        ratings_count
        reviews_count

        release_date
        release_year
        pages

        cached_contributors
        cached_tags

        image {
          url
          width
          height
        }
      }
    }
    """

    data = _graphql_request(
        query,
        {"id": book_id},
    )

    raw_book = data.get("books_by_pk")

    if not isinstance(raw_book, dict):
        return None

    image = raw_book.get("image") or {}
    slug = raw_book.get("slug")

    return {
        "id": raw_book.get("id"),
        "title": (
            raw_book.get("title")
            or "Unknown title"
        ),
        "subtitle": raw_book.get("subtitle"),
        "authors": _extract_authors(
            raw_book.get("cached_contributors")
        ),
        "description": raw_book.get("description"),
        "rating": raw_book.get("rating"),
        "ratings_count": (
            raw_book.get("ratings_count") or 0
        ),
        "reviews_count": (
            raw_book.get("reviews_count") or 0
        ),
        "release_date": raw_book.get("release_date"),
        "release_year": raw_book.get("release_year"),
        "pages": raw_book.get("pages"),
        "genres": _extract_tag_names(
            raw_book.get("cached_tags"),
            "Genre",
        ),
        "moods": _extract_tag_names(
            raw_book.get("cached_tags"),
            "Mood",
        ),
        "cover_url": image.get("url"),
        "slug": slug,
        "hardcover_url": (
            f"https://hardcover.app/books/{slug}"
            if slug
            else None
        ),
    }