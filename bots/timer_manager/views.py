"""Interactive controls for Discord timers."""

import discord

from .models import Timer, TimerStatus
from .timers import (
    InvalidTimerStateError,
    TimerManager,
    TimerNotFoundError,
    TimerPermissionError,
)
from .utils import format_duration, parse_duration


class AddTimeModal(discord.ui.Modal, title="Add Time"):
    """Modal used to extend an active timer."""

    duration = discord.ui.TextInput(
        label="Additional duration",
        placeholder="Examples: 5m, 1h 30m",
        max_length=50,
    )

    def __init__(
        self,
        timer_id: str,
        timer_manager: TimerManager,
    ) -> None:
        super().__init__()

        self.timer_id = timer_id
        self.timer_manager = timer_manager

    async def on_submit(
        self,
        interaction: discord.Interaction,
    ) -> None:
        try:
            seconds = parse_duration(str(self.duration))

            timer = self.timer_manager.add_time(
                timer_id=self.timer_id,
                user_id=interaction.user.id,
                seconds=seconds,
            )

        except (
            ValueError,
            TimerNotFoundError,
            TimerPermissionError,
            InvalidTimerStateError,
        ) as error:
            await interaction.response.send_message(
                f"❌ {error}",
                ephemeral=True,
            )
            return

        await update_timer_message(interaction, timer)

        await interaction.followup.send(
            f"➕ Added **{format_duration(seconds)}** to "
            f"**{timer.label}**.",
            ephemeral=True,
        )


class TimerView(discord.ui.View):
    """Pause, resume, extend, or cancel a timer."""

    def __init__(
        self,
        timer_id: str,
        timer_manager: TimerManager,
    ) -> None:
        super().__init__(timeout=None)

        self.timer_id = timer_id
        self.timer_manager = timer_manager

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        """Restrict controls to the timer creator."""

        try:
            timer = self.timer_manager.get_timer(self.timer_id)
        except TimerNotFoundError as error:
            await interaction.response.send_message(
                f"❌ {error}",
                ephemeral=True,
            )
            return False

        if interaction.user.id != timer.creator_id:
            await interaction.response.send_message(
                "❌ Only the timer creator can control this timer.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="Pause",
        emoji="⏸️",
        style=discord.ButtonStyle.secondary,
    )
    async def pause(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        try:
            timer = self.timer_manager.pause_timer(
                timer_id=self.timer_id,
                user_id=interaction.user.id,
            )
        except (
            TimerNotFoundError,
            TimerPermissionError,
            InvalidTimerStateError,
        ) as error:
            await interaction.response.send_message(
                f"❌ {error}",
                ephemeral=True,
            )
            return

        await update_timer_message(interaction, timer, view=self)

    @discord.ui.button(
        label="Resume",
        emoji="▶️",
        style=discord.ButtonStyle.success,
    )
    async def resume(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        try:
            timer = self.timer_manager.resume_timer(
                timer_id=self.timer_id,
                user_id=interaction.user.id,
            )
        except (
            TimerNotFoundError,
            TimerPermissionError,
            InvalidTimerStateError,
        ) as error:
            await interaction.response.send_message(
                f"❌ {error}",
                ephemeral=True,
            )
            return

        await update_timer_message(interaction, timer, view=self)

    @discord.ui.button(
        label="Add Time",
        emoji="➕",
        style=discord.ButtonStyle.primary,
    )
    async def add_time(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await interaction.response.send_modal(
            AddTimeModal(
                timer_id=self.timer_id,
                timer_manager=self.timer_manager,
            )
        )

    @discord.ui.button(
        label="Cancel",
        emoji="🛑",
        style=discord.ButtonStyle.danger,
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        try:
            timer = self.timer_manager.cancel_timer(
                timer_id=self.timer_id,
                user_id=interaction.user.id,
            )
        except (
            TimerNotFoundError,
            TimerPermissionError,
            InvalidTimerStateError,
        ) as error:
            await interaction.response.send_message(
                f"❌ {error}",
                ephemeral=True,
            )
            return

        self.disable_all_items()

        await update_timer_message(interaction, timer, view=self)

    def disable_all_items(self) -> None:
        """Disable every button in the view."""

        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True


async def update_timer_message(
    interaction: discord.Interaction,
    timer: Timer,
    *,
    view: TimerView | None = None,
) -> None:
    """Update an existing timer embed."""

    if interaction.message is None or not interaction.message.embeds:
        await interaction.response.send_message(
            "❌ The timer message could not be updated.",
            ephemeral=True,
        )
        return

    embed = interaction.message.embeds[0].copy()

    status_names = {
        TimerStatus.RUNNING: "Running",
        TimerStatus.PAUSED: "Paused",
        TimerStatus.COMPLETED: "Completed",
        TimerStatus.CANCELLED: "Cancelled",
    }

    colours = {
        TimerStatus.RUNNING: discord.Colour.blurple(),
        TimerStatus.PAUSED: discord.Colour.orange(),
        TimerStatus.COMPLETED: discord.Colour.green(),
        TimerStatus.CANCELLED: discord.Colour.red(),
    }

    embed.colour = colours[timer.status]
    embed.description = f"Timer is currently **{status_names[timer.status]}**."

    for index, field in enumerate(embed.fields):
        if field.name == "Status":
            embed.set_field_at(
                index,
                name="Status",
                value=status_names[timer.status],
                inline=field.inline,
            )

        elif field.name == "Duration":
            embed.set_field_at(
                index,
                name="Duration",
                value=format_duration(timer.duration_seconds),
                inline=field.inline,
            )

        elif field.name == "Countdown":
            embed.set_field_at(
                index,
                name="Countdown",
                value=format_duration(timer.get_remaining_seconds()),
                inline=field.inline,
            )

        elif field.name == "Finishes":
            if timer.end_time is not None:
                timestamp = int(timer.end_time.timestamp())
                value = f"<t:{timestamp}:F>\n<t:{timestamp}:R>"
            elif timer.status == TimerStatus.PAUSED:
                value = (
                    f"Paused with "
                    f"**{format_duration(timer.get_remaining_seconds())}** "
                    f"remaining"
                )
            else:
                value = "—"

            embed.set_field_at(
                index,
                name="Finishes",
                value=value,
                inline=field.inline,
            )

    await interaction.response.edit_message(
        embed=embed,
        view=view,
    )