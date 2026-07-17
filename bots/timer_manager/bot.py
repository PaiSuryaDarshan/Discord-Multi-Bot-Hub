"""Timer Manager extension setup."""

from discord.ext import commands

from .commands import TimerCommands
from .timers import TimerManager


async def setup(bot: commands.Bot) -> None:
    """Load Timer Manager into the Discord bot."""

    timer_manager = TimerManager()

    await bot.add_cog(
        TimerCommands(
            bot=bot,
            timer_manager=timer_manager,
        )
    )