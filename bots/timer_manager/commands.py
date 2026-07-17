"""Slash commands for Timer Manager."""

import discord
from discord import app_commands
from discord.ext import commands

from .timers import TimerManager
from .utils import format_countdown, format_duration, parse_duration

# Replace with your #timer-tool channel ID
TIMER_CHANNEL_ID = 1527762004171952139  


class TimerCommands(
    commands.GroupCog,
    group_name="timer",
    group_description="Create and manage Discord timers.",
):
    """Discord slash commands for Timer Manager."""

    def __init__(
        self,
        bot: commands.Bot,
        timer_manager: TimerManager,
    ) -> None:
        self.bot = bot
        self.timer_manager = timer_manager

    @app_commands.command(
        name="start",
        description="Start a new timer.",
    )
    @app_commands.describe(
        duration="Timer duration, such as 30s, 5m, 1h 30m, or 2d.",
        label="Optional name for the timer.",
        notify="Optional member to notify when the timer finishes.",
    )
    @app_commands.guild_only()
    async def start_timer(
        self,
        interaction: discord.Interaction,
        duration: str,
        label: str | None = None,
        notify: discord.Member | None = None,
    ) -> None:
        """Create a timer from a Discord slash command."""

        if interaction.channel_id != TIMER_CHANNEL_ID:
            await interaction.response.send_message(
                f"❌ Timer commands can only be used in <#{TIMER_CHANNEL_ID}>.",
                ephemeral=True,
            )
            return

        try:
            duration_seconds = parse_duration(duration)
        except ValueError as error:
            await interaction.response.send_message(
                f"❌ {error}\n\n"
                "**Examples:**\n"
                "`30s`\n"
                "`5m`\n"
                "`1h 30m`\n"
                "`2d`",
                ephemeral=True,
            )
            return

        creator = interaction.user
        notify_user = notify or creator

        timer = self.timer_manager.create_timer(
            creator_id=creator.id,
            notify_user_id=notify_user.id,
            channel_id=interaction.channel_id,
            duration_seconds=duration_seconds,
            label=label or "Timer",
        )

        if timer.end_time is None:
            await interaction.response.send_message(
                "❌ The timer could not be started.",
                ephemeral=True,
            )
            return

        finish_timestamp = int(timer.end_time.timestamp())

        embed = discord.Embed(
            title=f"⏱️ {timer.label}",
            description="Timer successfully started.",
            colour=discord.Colour.blurple(),
        )

        embed.add_field(
            name="Duration",
            value=format_duration(duration_seconds),
            inline=True,
        )
        embed.add_field(
            name="Countdown",
            value=format_countdown(duration_seconds),
            inline=True,
        )
        embed.add_field(
            name="Status",
            value="Running",
            inline=True,
        )
        embed.add_field(
            name="Finishes",
            value=f"<t:{finish_timestamp}:F>\n<t:{finish_timestamp}:R>",
            inline=False,
        )
        embed.add_field(
            name="Started by",
            value=creator.mention,
            inline=True,
        )
        embed.add_field(
            name="Notify",
            value=notify_user.mention,
            inline=True,
        )

        embed.set_footer(text=f"Timer ID: {timer.timer_id}")

        await interaction.response.send_message(embed=embed)

        message = await interaction.original_response()

        self.timer_manager.set_message_id(
            timer_id=timer.timer_id,
            message_id=message.id,
        )