import asyncio
import os

from common.webserver import keep_alive

from bots.welcomer.bot import create_bot as create_welcomer_bot

# Later:
# from bots.kaggle.bot import create_bot as create_kaggle_bot
# from bots.leetcode.bot import create_bot as create_leetcode_bot

async def main():
    keep_alive()  # <-- Start Flask once

    welcomer = create_welcomer_bot()

    await asyncio.gather(
        welcomer.start(os.environ["WELCOMER_BOT_TOKEN"]),
    )

if __name__ == "__main__":
    asyncio.run(main())