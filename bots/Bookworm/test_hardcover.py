import os
import sys
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv()

API_URL = "https://api.hardcover.app/v1/graphql"
TOKEN = os.getenv("HARDCOVER_API_TOKEN")


# Replace this with the ID returned for the correct search result.
BOOK_ID = 436358  # Example only — use the real Sapiens ID from your response.


def graphql_request(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    """Send a GraphQL request to Hardcover and return the response data."""

    if not TOKEN:
        print("Error: HARDCOVER_API_TOKEN is missing from .env")
        sys.exit(1)

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

        response.raise_for_status()

    except requests.RequestException as error:
        print(f"Request failed: {error}")
        sys.exit(1)

    try:
        payload = response.json()
    except requests.JSONDecodeError:
        print("Error: Hardcover returned invalid JSON.")
        print(response.text)
        sys.exit(1)

    if payload.get("errors"):
        print("GraphQL error:")
        for error in payload["errors"]:
            print(f"- {error.get('message', error)}")
        sys.exit(1)

    data = payload.get("data")

    if not isinstance(data, dict):
        print("Error: Hardcover returned no usable data.")
        print(payload)
        sys.exit(1)

    print(f"Status: {response.status_code}")

    return data


def extract_tag_names(cached_tags: Any, category: str) -> list[str]:
    """
    Extract genre or mood names from Hardcover's cached_tags JSON.

    The exact JSON shape may vary, so this handles several likely formats.
    """

    if not cached_tags:
        return []

    category_lower = category.lower()
    values: Any = None

    if isinstance(cached_tags, dict):
        for key, value in cached_tags.items():
            if str(key).lower() == category_lower:
                values = value
                break

    if not values:
        return []

    if isinstance(values, dict):
        values = list(values.values())

    if not isinstance(values, list):
        return []

    names: list[str] = []

    for item in values:
        if isinstance(item, str):
            names.append(item)

        elif isinstance(item, dict):
            name = (
                item.get("tag")
                or item.get("name")
                or item.get("text")
                or item.get("value")
            )

            if name:
                names.append(str(name))

    return list(dict.fromkeys(names))


def extract_authors(cached_contributors: Any) -> list[str]:
    """Extract author names from Hardcover's cached contributor data."""

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

        contribution_type = (
            contributor.get("contribution")
            or contributor.get("type")
            or ""
        )

        # Keep normal authors, but ignore obvious non-author roles.
        ignored_roles = {
            "translator",
            "illustrator",
            "editor",
            "narrator",
            "foreword",
        }

        if name and str(contribution_type).lower() not in ignored_roles:
            authors.append(str(name))

    return list(dict.fromkeys(authors))


def main() -> None:
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
        links

        image {
          url
          width
          height
          ratio
        }

        editions(limit: 20) {
          id
          isbn_10
          isbn_13
          pages
          release_date
          release_year
          edition_format
          physical_format
        }
      }
    }
    """

    data = graphql_request(
        query=query,
        variables={"id": BOOK_ID},
    )

    book = data.get("books_by_pk")

    if not book:
        print(f"No book found with ID {BOOK_ID}.")
        return

    title = book.get("title") or "Unknown title"
    subtitle = book.get("subtitle")
    authors = extract_authors(book.get("cached_contributors"))
    description = book.get("description")

    rating = book.get("rating")
    ratings_count = book.get("ratings_count") or 0
    reviews_count = book.get("reviews_count") or 0

    release_date = book.get("release_date")
    release_year = book.get("release_year")
    pages = book.get("pages")

    cached_tags = book.get("cached_tags")
    genres = extract_tag_names(cached_tags, "Genre")
    moods = extract_tag_names(cached_tags, "Mood")

    image = book.get("image") or {}
    cover_url = image.get("url")

    editions = book.get("editions") or []

    isbns = sorted(
        {
            isbn
            for edition in editions
            for isbn in (
                edition.get("isbn_10"),
                edition.get("isbn_13"),
            )
            if isbn
        }
    )

    slug = book.get("slug")
    hardcover_url = (
        f"https://hardcover.app/books/{slug}"
        if slug
        else None
    )

    print(f"\nTitle: {title}")

    if subtitle:
        print(f"Subtitle: {subtitle}")

    print(
        "Authors:",
        ", ".join(authors) if authors else "Not available",
    )

    if rating is not None:
        print(f"Rating: {float(rating):.2f} ({ratings_count} ratings)")
    else:
        print("Rating: Not available")

    print(f"Reviews: {reviews_count}")

    if release_date:
        print(f"Release date: {release_date}")
    elif release_year:
        print(f"Release year: {release_year}")
    else:
        print("Release date: Not available")

    print(f"Pages: {pages or 'Not available'}")

    print(
        "Genres:",
        ", ".join(genres) if genres else "Not available",
    )

    print(
        "Moods:",
        ", ".join(moods) if moods else "Not available",
    )

    print(
        "ISBNs:",
        ", ".join(isbns) if isbns else "Not available",
    )

    print(f"Cover image: {cover_url or 'Not available'}")
    print(f"Hardcover page: {hardcover_url or 'Not available'}")

    print("\nDescription:")
    print(description or "Not available")

    print("\nRetrieval confirmation:")
    checks = {
        "Title": bool(book.get("title")),
        "Authors": bool(authors),
        "Description": bool(description),
        "Cover image": bool(cover_url),
        "Rating": rating is not None,
        "Ratings count": book.get("ratings_count") is not None,
        "Reviews count": book.get("reviews_count") is not None,
        "Release information": bool(release_date or release_year),
        "Pages": pages is not None,
        "Genres": bool(genres),
        "Moods": bool(moods),
        "ISBNs": bool(isbns),
        "Hardcover link": bool(hardcover_url),
    }

    for field, available in checks.items():
        status = "✓ available" if available else "— unavailable"
        print(f"  {field}: {status}")

    print("\nRaw cached tags:")
    print(cached_tags)

    print("\nRaw image object:")
    print(image)


if __name__ == "__main__":
    main()