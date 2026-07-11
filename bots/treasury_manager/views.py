"""Moderator review controls for Treasury Manager requests."""

import asyncio
import logging
from collections.abc import Callable

import discord

from .embeds import (
    build_approved_embed,
    build_awaiting_embed,
    build_rejected_embed,
)
from .utils import generate_transaction_key


logger = logging.getLogger(__name__)


class TransactionReviewView(discord.ui.View):
    """Provide single-use moderator decisions for a transaction request."""

    def __init__(
        self,
        *,
        requester_id: int,
        approver_role_name: str = "Treasury Approver",
        amount_currency: str,
        market_pair: str,
        proposed_action: str,
        confidence_holding_period: str,
        thesis_risk_limit: str,
    ) -> None:
        """Store the requester and original request details for review."""
        super().__init__(timeout=86_400)
        self.requester_id = requester_id
        self.approver_role_name = approver_role_name
        self.request_details = {
            "amount_currency": amount_currency,
            "market_pair": market_pair,
            "proposed_action": proposed_action,
            "confidence_holding_period": confidence_holding_period,
            "thesis_risk_limit": thesis_risk_limit,
        }
        self.completed = False
        self._decision_lock = asyncio.Lock()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Allow only configured approvers or server administrators."""
        member = interaction.user
        is_approver = isinstance(member, discord.Member) and (
            member.guild_permissions.administrator
            or discord.utils.get(
                member.roles,
                name=self.approver_role_name,
            )
            is not None
        )

        if not is_approver:
            await interaction.response.send_message(
                f"You need the {self.approver_role_name!r} role or administrator "
                "permissions to review this request.",
                ephemeral=True,
            )
            return False

        if self.completed:
            await interaction.response.send_message(
                "This transaction request has already been processed.",
                ephemeral=True,
            )
            return False

        return True

    def _disable_buttons(self) -> None:
        """Disable every button after a terminal review decision."""
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    async def _apply_decision(
        self,
        interaction: discord.Interaction,
        build_embed: Callable[[], discord.Embed],
    ) -> None:
        """Atomically apply one decision and update the original message."""
        async with self._decision_lock:
            if self.completed:
                await interaction.response.send_message(
                    "This transaction request has already been processed.",
                    ephemeral=True,
                )
                return

            try:
                embed = build_embed()
                self._disable_buttons()
                await interaction.response.edit_message(embed=embed, view=self)
            except Exception:
                logger.exception(
                    "[Treasury Manager] Failed to apply a review decision."
                )
                for item in self.children:
                    if isinstance(item, discord.ui.Button):
                        item.disabled = False
                await self._send_error(interaction)
                return

            self.completed = True

    @staticmethod
    async def _send_error(interaction: discord.Interaction) -> None:
        """Acknowledge a failed decision without exposing details publicly."""
        message = "I could not update this request. Please try again later."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)

    @discord.ui.button(
        label="Approve",
        style=discord.ButtonStyle.green,
        emoji="✅",
    )
    async def approve(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button["TransactionReviewView"],
    ) -> None:
        """Approve the request and generate an authorisation key."""
        del button

        def build_embed() -> discord.Embed:
            return build_approved_embed(
                requester_id=self.requester_id,
                approver=interaction.user,
                amount_currency=self.request_details["amount_currency"],
                market_pair=self.request_details["market_pair"],
                proposed_action=self.request_details["proposed_action"],
                transaction_key=generate_transaction_key(),
            )

        await self._apply_decision(interaction, build_embed)

    @discord.ui.button(
        label="Await",
        style=discord.ButtonStyle.secondary,
        emoji="⏳",
    )
    async def await_information(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button["TransactionReviewView"],
    ) -> None:
        """Place the request on hold without generating a transaction key."""
        del button
        await self._apply_decision(
            interaction,
            lambda: build_awaiting_embed(
                requester_id=self.requester_id,
                reviewer=interaction.user,
                request_details=self.request_details,
            ),
        )

    @discord.ui.button(
        label="Reject",
        style=discord.ButtonStyle.red,
        emoji="❌",
    )
    async def reject(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button["TransactionReviewView"],
    ) -> None:
        """Reject the request without generating a transaction key."""
        del button
        await self._apply_decision(
            interaction,
            lambda: build_rejected_embed(
                requester_id=self.requester_id,
                reviewer=interaction.user,
                request_details=self.request_details,
            ),
        )

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item["TransactionReviewView"],
    ) -> None:
        """Log unexpected view errors and acknowledge the interaction."""
        logger.error(
            "[Treasury Manager] Unexpected review view error from %r.",
            item,
            exc_info=(type(error), error, error.__traceback__),
        )
        await self._send_error(interaction)
