"""Discord client setup for Timer Manager."""

import discord
from discord.ext import commands

from .commands import TimerCommands
from .timers import TimerManager


class TimerManagerBot(commands.Bot):
    """Discord bot responsible for timer commands and interactions."""

    def __init__(self) -> None:
        intents = discord.Intents.default()

        super().__init__(
            command_prefix="!",
            intents=intents,
        )

        self.timer_manager = TimerManager()

    async def setup_hook(self) -> None:
        """Register commands and sync the application-command tree."""

        await self.add_cog(
            TimerCommands(
                bot=self,
                timer_manager=self.timer_manager,
            )
        )

        await self.tree.sync()

    async def on_ready(self) -> None:
        """Log when the bot successfully connects to Discord."""

        if self.user is not None:
            print(f"Timer Manager connected as {self.user}")


def create_bot() -> TimerManagerBot:
    """Create and return the Timer Manager Discord client."""

    return TimerManagerBot()