"""Discord client for the demonstration Treasury Manager workflow."""

import logging

import discord
from discord import app_commands

from .modals import TransactionRequestModal


TREASURY_MEMBER_ROLE = "Treasury Member"
TREASURY_APPROVER_ROLE = "Treasury Approver"

logger = logging.getLogger(__name__)


def _is_authorised_requester(member: discord.Member) -> bool:
    """Return whether a member may submit a transaction request."""
    return (
        member.guild_permissions.administrator
        or discord.utils.get(member.roles, name=TREASURY_MEMBER_ROLE) is not None
    )


class TreasuryManagerClient(discord.Client):
    """Discord client that collects dummy requests for moderator review."""

    def __init__(self) -> None:
        """Initialise the client and its application command tree."""
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self._register_commands()

    def _register_commands(self) -> None:
        """Register Treasury Manager application commands."""

        @self.tree.command(
            name="request_transaction",
            description="Submit a dummy transaction request for moderator review.",
        )
        @app_commands.guild_only()
        async def request_transaction(interaction: discord.Interaction) -> None:
            """Open the transaction request form for an authorised member."""
            if not isinstance(interaction.user, discord.Member):
                await interaction.response.send_message(
                    "This command can only be used in a Discord server.",
                    ephemeral=True,
                )
                return

            if not _is_authorised_requester(interaction.user):
                await interaction.response.send_message(
                    f"You need the {TREASURY_MEMBER_ROLE!r} role or administrator "
                    "permissions to submit a transaction request.",
                    ephemeral=True,
                )
                return

            try:
                await interaction.response.send_modal(
                    TransactionRequestModal(
                        approver_role_name=TREASURY_APPROVER_ROLE,
                    )
                )
            except discord.HTTPException:
                logger.exception(
                    "[Treasury Manager] Failed to open the transaction request modal."
                )
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "The transaction request form could not be opened. "
                        "Please try again later.",
                        ephemeral=True,
                    )

    async def setup_hook(self) -> None:
        """Synchronise application commands before the client becomes ready."""
        try:
            synced_commands = await self.tree.sync()
        except discord.HTTPException:
            logger.exception(
                "[Treasury Manager] Failed to synchronise application commands."
            )
            raise

        logger.info(
            "[Treasury Manager] Synchronised %d application command(s).",
            len(synced_commands),
        )

    async def on_ready(self) -> None:
        """Log that the Treasury Manager client connected successfully."""
        logger.info("[Treasury Manager] Logged in successfully as %s.", self.user)


def create_bot() -> TreasuryManagerClient:
    """Create an unstarted Treasury Manager Discord client."""
    return TreasuryManagerClient()
