"""Slash commands for Timer Manager."""

import re

import discord
from discord import app_commands
from discord.ext import commands

from .timers import TimerManager
from .views import PomodoroView, TimerView, build_pomodoro_embed
from .utils import format_countdown, format_duration, parse_duration

# Replace with your #timer-tool channel ID
TIMER_CHANNEL_ID = 1527762004171952139  
MENTION_PATTERN = re.compile(r"<@(?P<user>!?\d+)>|<@&(?P<role>\d+)>")
MENTION_SEPARATOR_PATTERN = re.compile(r"^[\s,]*$")
MAX_NOTIFICATION_TARGETS = 20


def parse_notification_targets(
    value: str,
    guild: discord.Guild,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Parse and validate member and role mentions from a command option."""

    user_ids: list[int] = []
    role_ids: list[int] = []
    cursor = 0

    for match in MENTION_PATTERN.finditer(value):
        if not MENTION_SEPARATOR_PATTERN.fullmatch(value[cursor:match.start()]):
            raise ValueError("Only member and role mentions are allowed.")

        if match.group("user") is not None:
            user_id = int(match.group("user").lstrip("!"))

            if user_id not in user_ids:
                user_ids.append(user_id)
        else:
            role_id = int(match.group("role"))
            role = guild.get_role(role_id)

            if role is None or role.is_default():
                raise ValueError(f"<@&{role_id}> is not a valid server role.")

            if role_id not in role_ids:
                role_ids.append(role_id)

        cursor = match.end()

    if not MENTION_SEPARATOR_PATTERN.fullmatch(value[cursor:]):
        raise ValueError("Only member and role mentions are allowed.")

    if not user_ids and not role_ids:
        raise ValueError("Mention at least one member or role.")

    if len(user_ids) + len(role_ids) > MAX_NOTIFICATION_TARGETS:
        raise ValueError(
            f"You can notify up to {MAX_NOTIFICATION_TARGETS} members and roles."
        )

    return tuple(user_ids), tuple(role_ids)


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
        name="pomodoro",
        description="Start an automatic focus and break cycle.",
    )
    @app_commands.describe(
        focus="Focus duration (default: 25m).",
        short_break="Short-break duration (default: 5m).",
        sessions="Number of focus sessions (default: 4).",
        long_break="Final long-break duration (default: 15m).",
        notify="User to notify when each phase ends (default: you).",
    )
    @app_commands.guild_only()
    async def pomodoro(
        self,
        interaction: discord.Interaction,
        focus: str = "25m",
        short_break: str = "5m",
        sessions: app_commands.Range[int, 1, 20] = 4,
        long_break: str = "15m",
        notify: discord.Member | None = None,
    ) -> None:
        """Start an automatically advancing Pomodoro cycle."""

        if interaction.channel_id != TIMER_CHANNEL_ID:
            await interaction.response.send_message(
                f"❌ Timer commands can only be used in <#{TIMER_CHANNEL_ID}>.",
                ephemeral=True,
            )
            return

        try:
            focus_seconds = parse_duration(focus)
            short_break_seconds = parse_duration(short_break)
            long_break_seconds = parse_duration(long_break)
        except ValueError as error:
            await interaction.response.send_message(f"❌ {error}", ephemeral=True)
            return

        notify_user = notify or interaction.user
        timer = self.timer_manager.create_pomodoro(
            creator_id=interaction.user.id,
            notify_user_id=notify_user.id,
            channel_id=interaction.channel_id,
            focus_seconds=focus_seconds,
            short_break_seconds=short_break_seconds,
            long_break_seconds=long_break_seconds,
            sessions=sessions,
        )
        view = PomodoroView(timer.timer_id, self.timer_manager)
        await interaction.response.send_message(
            embed=build_pomodoro_embed(timer),
            view=view,
        )
        message = await interaction.original_response()
        self.timer_manager.set_message_id(timer.timer_id, message.id)

    @app_commands.command(
        name="start",
        description="Start a new timer.",
    )
    @app_commands.describe(
        duration="Timer duration, such as 30s, 5m, 1h 30m, or 2d.",
        label="Name for the timer.",
        notify="Optional member/role mentions, separated by spaces.",
    )
    @app_commands.guild_only()
    async def start_timer(
        self,
        interaction: discord.Interaction,
        duration: str,
        label: str,
        notify: str | None = None,
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

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Timers can only be created inside a server.",
                ephemeral=True,
            )
            return

        if notify is None:
            notify_user_ids = (creator.id,)
            notify_role_ids: tuple[int, ...] = ()
        else:
            try:
                notify_user_ids, notify_role_ids = parse_notification_targets(
                    notify,
                    interaction.guild,
                )
            except ValueError as error:
                await interaction.response.send_message(
                    f"❌ {error}\n\n"
                    "Mention people and roles separated by spaces, for example: "
                    "`@Alice @Bob @TeamRole`.",
                    ephemeral=True,
                )
                return

            for user_id in notify_user_ids:
                if interaction.guild.get_member(user_id) is not None:
                    continue

                try:
                    await interaction.guild.fetch_member(user_id)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    await interaction.response.send_message(
                        f"❌ <@{user_id}> is not a member of this server.",
                        ephemeral=True,
                    )
                    return

        notify_mentions = [
            *(f"<@{user_id}>" for user_id in notify_user_ids),
            *(f"<@&{role_id}>" for role_id in notify_role_ids),
        ]

        timer = self.timer_manager.create_timer(
            creator_id=creator.id,
            notify_user_ids=notify_user_ids,
            notify_role_ids=notify_role_ids,
            channel_id=interaction.channel_id,
            duration_seconds=duration_seconds,
            label=label,
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
            value=" ".join(notify_mentions),
            inline=True,
        )

        embed.set_footer(text=f"Timer ID: {timer.timer_id}")

        view = TimerView(
            timer_id=timer.timer_id,
            timer_manager=self.timer_manager,
        )

        await interaction.response.send_message(
            embed=embed,
            view=view,
        )

        message = await interaction.original_response()

        self.timer_manager.set_message_id(
            timer_id=timer.timer_id,
            message_id=message.id,
        )
