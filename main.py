import asyncio
import os

from common.webserver import keep_alive

from bots.treasury_manager import create_bot as create_treasury_manager_bot
from bots.welcomer.bot import create_bot as create_welcomer_bot

# Later:
# from bots.kaggle.bot import create_bot as create_kaggle_bot
# from bots.leetcode.bot import create_bot as create_leetcode_bot

async def main() -> None:
    """Start the shared web server and all configured Discord clients."""
    keep_alive()

    welcomer = create_welcomer_bot()
    treasury_manager = create_treasury_manager_bot()

    await asyncio.gather(
        welcomer.start(os.environ["WELCOMER_BOT_TOKEN"]),
        treasury_manager.start(os.environ["TREASURY_MANAGER_BOT_TOKEN"]),
    )


if __name__ == "__main__":
    asyncio.run(main())
