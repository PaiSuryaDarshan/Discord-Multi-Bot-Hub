"""Small shared utilities for the dummy Treasury Manager bot."""

import secrets


def generate_transaction_key() -> str:
    """Return a demonstration authorisation reference, not a real transaction.

    The generated value does not create, sign, broadcast, or represent a
    blockchain transaction.
    """
    groups = (secrets.token_hex(2).upper() for _ in range(3))
    return f"TX-{'-'.join(groups)}"


def truncate_text(value: str, limit: int) -> str:
    """Fit text within a limit, appending an ellipsis when it is truncated."""
    if limit < 0:
        raise ValueError("limit must be zero or greater")
    if len(value) <= limit:
        return value
    if limit <= 3:
        return "." * limit
    return f"{value[: limit - 3]}..."
