"""Embed builders for the demonstration Treasury Manager workflow."""

from collections.abc import Mapping

import discord

from .utils import truncate_text


EMBED_FIELD_LIMIT = 1_024
FOOTER_TEXT = "Demonstration workflow only — no funds are transferred."


def _truncate(value: object, limit: int = EMBED_FIELD_LIMIT) -> str:
    """Convert a value to text and truncate it without exceeding a limit."""
    text = str(value).strip() or "Not provided"
    return truncate_text(text, limit)


def _mention(user_or_id: discord.abc.User | int) -> str:
    """Return a Discord mention for a user object or user ID."""
    user_id = user_or_id if isinstance(user_or_id, int) else user_or_id.id
    return f"<@{user_id}>"


def _base_embed(title: str, color: discord.Color) -> discord.Embed:
    """Create an embed with the workflow's common metadata."""
    embed = discord.Embed(
        title=title,
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text=FOOTER_TEXT)
    return embed


def _request_summary(request_details: Mapping[str, str]) -> str:
    """Build a compact amount, market, and action summary."""
    amount = request_details.get("amount_currency", "Not provided")
    market = request_details.get("market_pair", "Not provided")
    action = request_details.get("proposed_action", "Not provided")
    return _truncate(f"{amount} • {market} • {action}")


def build_pending_embed(
    *,
    requester: discord.abc.User,
    amount_currency: str,
    market_pair: str,
    proposed_action: str,
    confidence_holding_period: str,
    thesis_risk_limit: str,
) -> discord.Embed:
    """Build the detailed embed shown while a request awaits review."""
    embed = _base_embed("Transaction Request", discord.Color.gold())
    fields = (
        ("Requester", _mention(requester), False),
        ("Amount and Currency", _truncate(amount_currency), True),
        ("Market or Trading Pair", _truncate(market_pair), True),
        ("Proposed Action", _truncate(proposed_action), True),
        (
            "Confidence and Holding Period",
            _truncate(confidence_holding_period),
            True,
        ),
        ("Trade Thesis and Risk Limit", _truncate(thesis_risk_limit), False),
        ("Status", "Awaiting Review", False),
    )
    for name, value, inline in fields:
        embed.add_field(name=name, value=value, inline=inline)
    return embed


def build_approved_embed(
    *,
    requester_id: int,
    approver: discord.abc.User,
    amount_currency: str,
    market_pair: str,
    proposed_action: str,
    transaction_key: str,
) -> discord.Embed:
    """Build a compact embed for an approved dummy request."""
    embed = _base_embed("✅ Transaction Approved", discord.Color.green())
    fields = (
        ("Requester", _mention(requester_id)),
        ("Approver", _mention(approver)),
        ("Amount", _truncate(amount_currency)),
        ("Market", _truncate(market_pair)),
        ("Action", _truncate(proposed_action)),
        ("Authorisation Key", _truncate(transaction_key)),
    )
    for name, value in fields:
        embed.add_field(name=name, value=value, inline=True)
    return embed


def build_awaiting_embed(
    *,
    requester_id: int,
    reviewer: discord.abc.User,
    request_details: Mapping[str, str],
) -> discord.Embed:
    """Build an embed for a request awaiting further information."""
    embed = _base_embed(
        "⏳ Awaiting Further Information",
        discord.Color.orange(),
    )
    embed.add_field(name="Requester", value=_mention(requester_id), inline=True)
    embed.add_field(name="Reviewer", value=_mention(reviewer), inline=True)
    embed.add_field(
        name="Request Summary",
        value=_request_summary(request_details),
        inline=False,
    )
    return embed


def build_rejected_embed(
    *,
    requester_id: int,
    reviewer: discord.abc.User,
    request_details: Mapping[str, str],
) -> discord.Embed:
    """Build a compact embed for a rejected dummy request."""
    embed = _base_embed("❌ Transaction Rejected", discord.Color.red())
    embed.add_field(name="Requester", value=_mention(requester_id), inline=True)
    embed.add_field(name="Reviewer", value=_mention(reviewer), inline=True)
    embed.add_field(
        name="Request Summary",
        value=_request_summary(request_details),
        inline=False,
    )
    return embed
