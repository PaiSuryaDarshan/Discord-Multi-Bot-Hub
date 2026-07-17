"""Discord client setup for Timer Manager."""

import asyncio

import discord
from discord.ext import commands, tasks

from .commands import TimerCommands
from .models import Timer
from .timers import InvalidTimerStateError, TimerManager


COMPLETED_TIMER_LIFETIME_SECONDS = 60


class TimerManagerBot(commands.Bot):
    """Discord bot responsible for timer commands and completion alerts."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(
            command_prefix="!",
            intents=intents,
        )

        self.timer_manager = TimerManager()
        self._cleanup_tasks: set[asyncio.Task[None]] = set()

    async def setup_hook(self) -> None:
        """Register commands, sync them, and start the timer checker."""

        await self.add_cog(
            TimerCommands(
                bot=self,
                timer_manager=self.timer_manager,
            )
        )

        synced = await self.tree.sync()
        print(f"Synced {len(synced)} Timer Manager commands globally.")

        self.check_finished_timers.start()

    async def on_ready(self) -> None:
        """Log when the bot successfully connects to Discord."""

        if self.user is not None:
            print(f"Timer Manager connected as {self.user}")

    async def close(self) -> None:
        """Stop background tasks before disconnecting."""

        if self.check_finished_timers.is_running():
            self.check_finished_timers.cancel()

        cleanup_tasks = tuple(self._cleanup_tasks)

        for cleanup_task in cleanup_tasks:
            cleanup_task.cancel()

        if cleanup_tasks:
            await asyncio.gather(
                *cleanup_tasks,
                return_exceptions=True,
            )

        await super().close()

    @tasks.loop(seconds=2)
    async def check_finished_timers(self) -> None:
        """Check active timers and announce completed ones."""

        for timer in self.timer_manager.get_due_timers():
            try:
                self.timer_manager.complete_timer(timer.timer_id)
            except InvalidTimerStateError:
                continue

            channel = self.get_channel(timer.channel_id)

            if channel is None:
                try:
                    channel = await self.fetch_channel(timer.channel_id)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    print(
                        f"Could not access channel for timer "
                        f"{timer.timer_id}."
                    )
                    continue

            if not isinstance(channel, discord.TextChannel):
                continue

            await self._update_completed_message(channel, timer.message_id)
            self._schedule_timer_cleanup(channel, timer)
            await self._send_private_notifications(channel.guild, timer)

    @check_finished_timers.before_loop
    async def before_check_finished_timers(self) -> None:
        """Wait until Discord is connected before checking timers."""

        await self.wait_until_ready()

    async def _update_completed_message(
        self,
        channel: discord.TextChannel,
        message_id: int | None,
    ) -> None:
        """Update the original timer embed after completion."""

        if message_id is None:
            return

        try:
            message = await channel.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return

        if not message.embeds:
            return

        embed = message.embeds[0].copy()
        embed.description = "Timer completed."
        embed.colour = discord.Colour.green()

        for index, field in enumerate(embed.fields):
            if field.name == "Status":
                embed.set_field_at(
                    index,
                    name="Status",
                    value="Completed",
                    inline=field.inline,
                )
                break

        try:
            await message.edit(embed=embed)
        except discord.HTTPException:
            pass

    async def _send_private_notifications(
        self,
        guild: discord.Guild,
        timer: Timer,
    ) -> None:
        """DM the creator and every selected member or role member."""

        member_ids = {timer.creator_id, *timer.notify_user_ids}
        selected_role_ids = set(timer.notify_role_ids)

        if selected_role_ids:
            for role_id in selected_role_ids:
                role = guild.get_role(role_id)

                if role is not None:
                    member_ids.update(member.id for member in role.members)

            try:
                async for member in guild.fetch_members(limit=None):
                    if any(
                        role.id in selected_role_ids
                        for role in member.roles
                    ):
                        member_ids.add(member.id)
            except (discord.Forbidden, discord.HTTPException) as error:
                print(
                    "Could not retrieve every role member for timer "
                    f"{timer.timer_id}: {error}"
                )

        for member_id in member_ids:
            member = guild.get_member(member_id)

            if member is None:
                try:
                    member = await guild.fetch_member(member_id)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    continue

            if member.bot:
                continue

            try:
                await member.send(
                    f"⏰ **{timer.label}** has finished!\n"
                    f"This is a private notification from **{guild.name}**."
                )
            except (discord.Forbidden, discord.HTTPException) as error:
                print(
                    f"Could not privately notify member {member_id} "
                    f"for timer {timer.timer_id}: {error}"
                )

    def _schedule_timer_cleanup(
        self,
        channel: discord.TextChannel,
        timer: Timer,
    ) -> None:
        """Schedule deletion of a completed timer's original message."""

        cleanup_task = asyncio.create_task(
            self._delete_timer_message_after_delay(channel, timer),
            name=f"timer-cleanup-{timer.timer_id}",
        )
        self._cleanup_tasks.add(cleanup_task)
        cleanup_task.add_done_callback(self._cleanup_tasks.discard)

    async def _delete_timer_message_after_delay(
        self,
        channel: discord.TextChannel,
        timer: Timer,
    ) -> None:
        """Delete the timer message after the completed grace period."""

        await asyncio.sleep(COMPLETED_TIMER_LIFETIME_SECONDS)

        if timer.message_id is not None:
            try:
                message = await channel.fetch_message(timer.message_id)
                await message.delete()
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

        self.timer_manager.remove_timer(timer.timer_id)


def create_bot() -> TimerManagerBot:
    """Create and return the Timer Manager Discord client."""

    return TimerManagerBot()
