"""Small shared utilities for the Treasury Manager bot."""

import secrets


TRANSACTION_KEY_CANDIDATE_COUNT = 26


def _generate_key_candidate() -> str:
    """Generate one cryptographically random transaction key candidate."""
    groups = (secrets.token_hex(2).upper() for _ in range(3))
    return f"TX-{'-'.join(groups)}"


def generate_transaction_key() -> str:
    """Generate fresh candidates and securely select an authorisation key."""
    candidates = tuple(
        _generate_key_candidate()
        for _ in range(TRANSACTION_KEY_CANDIDATE_COUNT)
    )
    return secrets.choice(candidates)


def truncate_text(value: str, limit: int) -> str:
    """Fit text within a limit, appending an ellipsis when it is truncated."""
    if limit < 0:
        raise ValueError("limit must be zero or greater")
    if len(value) <= limit:
        return value
    if limit <= 3:
        return "." * limit
    return f"{value[: limit - 3]}..."
