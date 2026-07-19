# Implementation Considerations for Hardcover API

This document summarises the implementation decisions and considerations for integrating the Hardcover GraphQL API into the Discord Book Recommendation Bot.

---

# 1. Search → Fetch Architecture

The bot should use a **two-step retrieval process** rather than attempting to build the Discord embed directly from the search results.

```text
User types query
        ↓
Search Hardcover
        ↓
Display autocomplete suggestions
        ↓
User selects book
        ↓
Retrieve full book by ID
        ↓
Build Discord embed
```

This ensures the embed always uses the most complete and up-to-date metadata available.

---

# 2. Store the Book ID

Autocomplete should display a human-readable title, but internally store the **Hardcover Book ID**.

Example:

```text
Displayed:
Sapiens — Yuval Noah Harari

Stored:
30424
```

The Book ID is unique and should be used for all subsequent API requests.

---

# 3. Search Result Ranking

Search results may include:

- summaries
- study guides
- analyses
- review books

These should be ranked below the original work.

Current strategy:

- penalise titles containing words such as:
  - summary
  - analysis
  - review
  - key takeaways
  - study guide
- sort remaining results by ratings count.

---

# 4. Optional Fields

Not every Hardcover book contains every field.

The bot should gracefully omit unavailable information rather than displaying placeholder text.

Examples:

```python
if genres:
    ...

if moods:
    ...

if description:
    ...
```

The bot should never fail because an optional field is missing.

---

# 5. Description Length

Some descriptions are extremely long.

Discord embeds have field and total character limits.

Descriptions should therefore be truncated before being added to the embed.

Example:

```python
description = (book.get("description") or "").strip()

if len(description) > 1200:
    description = description[:1197] + "..."
```

---

# 6. ISBNs

Although Hardcover exposes ISBN-10 and ISBN-13 information, these are not particularly useful for a recommendation bot.

Recommendation:

- retrieve ISBNs if desired
- do not display them in the Discord embed

---

# 7. Genres and Moods

Books may contain many genres and moods.

Displaying all of them creates unnecessarily cluttered embeds.

Recommendation:

```python
genres = genres[:5]
moods = moods[:5]
```

---

# 8. Cover Image

Use the returned cover image URL directly as the embed thumbnail.

Example:

```python
embed.set_thumbnail(url=cover_image_url)
```

---

# 9. Hardcover Link

Always include the Hardcover page.

Construct using the returned slug:

```text
https://hardcover.app/books/{slug}
```

This provides users with an easy way to view additional information.

---

# 10. Language Considerations

Descriptions are not guaranteed to be English.

The API returns the stored description for the selected edition, which may be in another language.

The bot should display the description exactly as returned rather than attempting translation.

---

# 11. Verified Fields

The following fields have been successfully retrieved and verified.

| Field | Status |
|-------|--------|
| Book ID | ✓ |
| Title | ✓ |
| Subtitle | ✓ |
| Authors | ✓ |
| Description | ✓ |
| Cover image URL | ✓ |
| Rating | ✓ |
| Ratings count | ✓ |
| Reviews count | ✓ |
| Release date | ✓ |
| Release year | ✓ |
| Page count | ✓ |
| Genres | ✓ |
| Moods | ✓ |
| Hardcover slug | ✓ |
| Hardcover page URL | ✓ |
| ISBNs | ✓ |

---

# 12. Final Client Interface

The remainder of the project should never interact directly with GraphQL.

Instead, expose a simple client interface.

```python
search_books(search_term: str) -> list[Book]

get_book(book_id: int) -> Book
```

All GraphQL queries, HTTP requests, response parsing, validation, and error handling should remain encapsulated within the Hardcover client module.