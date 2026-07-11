"""Transaction request modal for the demonstration Treasury Manager bot."""

import logging

import discord

from .embeds import build_pending_embed
from .views import TransactionReviewView


REVIEW_CHANNEL_NAME = "treasury-requests"

logger = logging.getLogger(__name__)


class TransactionRequestModal(
    discord.ui.Modal,
    title="Request a Transaction Review",
):
    """Collect a dummy transaction proposal for moderator review."""

    def __init__(
        self,
        *,
        approver_role_name: str = "Treasury Approver",
    ) -> None:
        """Initialise the modal with the configured review role name."""
        super().__init__()
        self.approver_role_name = approver_role_name

    amount_currency = discord.ui.TextInput(
        label="Amount and currency",
        placeholder="250 USDC",
        min_length=1,
        max_length=100,
        required=True,
    )
    market_pair = discord.ui.TextInput(
        label="Market or trading pair",
        placeholder="BTC/USDT",
        min_length=1,
        max_length=100,
        required=True,
    )
    proposed_action = discord.ui.TextInput(
        label="Proposed action",
        placeholder="Long, Short, Buy, or Sell",
        min_length=1,
        max_length=100,
        required=True,
    )
    confidence_holding_period = discord.ui.TextInput(
        label="Confidence and holding period",
        placeholder="8/10, 2-5 days",
        min_length=1,
        max_length=150,
        required=True,
    )
    thesis_risk_limit = discord.ui.TextInput(
        label="Trade thesis and risk limit",
        placeholder="Explain the reasoning, invalidation point, or stop condition.",
        style=discord.TextStyle.paragraph,
        min_length=1,
        max_length=1500,
        required=True,
    )

    def _values(self) -> dict[str, str]:
        """Return normalised values entered in the modal."""
        return {
            "amount_currency": self.amount_currency.value.strip(),
            "market_pair": self.market_pair.value.strip(),
            "proposed_action": self.proposed_action.value.strip(),
            "confidence_holding_period": (
                self.confidence_holding_period.value.strip()
            ),
            "thesis_risk_limit": self.thesis_risk_limit.value.strip(),
        }

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Post the completed request to the configured review channel."""
        values = self._values()
        if any(not value for value in values.values()):
            await interaction.response.send_message(
                "Every transaction request field is required.",
                ephemeral=True,
            )
            return

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "Transaction requests can only be submitted from a server.",
                ephemeral=True,
            )
            return

        review_channel = discord.utils.get(
            guild.text_channels,
            name=REVIEW_CHANNEL_NAME,
        )
        bot_member = guild.me

        if review_channel is None or bot_member is None:
            await interaction.response.send_message(
                f"I could not find an accessible #{REVIEW_CHANNEL_NAME} channel. "
                "Please ask a server administrator to configure it.",
                ephemeral=True,
            )
            return

        permissions = review_channel.permissions_for(bot_member)
        if not (permissions.send_messages and permissions.embed_links):
            await interaction.response.send_message(
                f"I need permission to send messages and embeds in "
                f"#{REVIEW_CHANNEL_NAME}. Please contact a server administrator.",
                ephemeral=True,
            )
            return

        embed = build_pending_embed(
            requester=interaction.user,
            amount_currency=values["amount_currency"],
            market_pair=values["market_pair"],
            proposed_action=values["proposed_action"],
            confidence_holding_period=values["confidence_holding_period"],
            thesis_risk_limit=values["thesis_risk_limit"],
        )
        view = TransactionReviewView(
            requester_id=interaction.user.id,
            approver_role_name=self.approver_role_name,
            amount_currency=values["amount_currency"],
            market_pair=values["market_pair"],
            proposed_action=values["proposed_action"],
            confidence_holding_period=values["confidence_holding_period"],
            thesis_risk_limit=values["thesis_risk_limit"],
        )

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            await review_channel.send(embed=embed, view=view)
        except (discord.Forbidden, discord.HTTPException):
            logger.exception(
                "[Treasury Manager] Failed to post a transaction request in #%s.",
                REVIEW_CHANNEL_NAME,
            )
            await interaction.edit_original_response(
                content=(
                    "I could not submit your transaction request. Please try again "
                    "later or contact a server administrator."
                ),
            )
            return

        await interaction.edit_original_response(
            content="Your transaction request has been submitted for review.",
        )

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
    ) -> None:
        """Log unexpected modal errors and notify the requester privately."""
        logger.error(
            "[Treasury Manager] Unexpected transaction modal error.",
            exc_info=(type(error), error, error.__traceback__),
        )
        if interaction.response.is_done():
            await interaction.followup.send(
                "An unexpected error occurred while submitting your request.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "An unexpected error occurred while submitting your request.",
                ephemeral=True,
            )
