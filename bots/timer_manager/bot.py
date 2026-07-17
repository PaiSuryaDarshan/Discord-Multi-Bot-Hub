"""Discord client setup for Timer Manager."""

import discord
from discord.ext import commands, tasks

from .commands import TimerCommands
from .timers import InvalidTimerStateError, TimerManager


class TimerManagerBot(commands.Bot):
    """Discord bot responsible for timer commands and completion alerts."""

    def __init__(self) -> None:
        intents = discord.Intents.default()

        super().__init__(
            command_prefix="!",
            intents=intents,
        )

        self.timer_manager = TimerManager()

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

            notify_mentions = [
                *(f"<@{user_id}>" for user_id in timer.notify_user_ids),
                *(f"<@&{role_id}>" for role_id in timer.notify_role_ids),
            ]

            try:
                await channel.send(
                    f"⏰ {' '.join(notify_mentions)} — "
                    f"**{timer.label}** has finished!",
                    allowed_mentions=discord.AllowedMentions(
                        everyone=False,
                        users=True,
                        roles=True,
                    ),
                )
            except discord.HTTPException as error:
                print(
                    f"Failed to send completion message for "
                    f"timer {timer.timer_id}: {error}"
                )

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


def create_bot() -> TimerManagerBot:
    """Create and return the Timer Manager Discord client."""

    return TimerManagerBot()
