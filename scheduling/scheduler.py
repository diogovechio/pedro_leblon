import logging

import schedule

from pedro_leblon import FakePedro

from scheduling.bolso_counter import bosta_daily_counter
from scheduling.check_and_save_commemorations import check_and_save
from scheduling.commemorations import commemorations
from scheduling.daily_reset import daily_reset


async def scheduler(bot: FakePedro) -> None:
    # IMPORTANT: UNHANDLED EXCEPTIONS MAY BLOCK ALL OTHER SCHEDULES
    schedule.every(15).seconds.do(
        lambda: logging.info('Scheduling health check')
    )

    schedule.every().day.do(
        daily_reset, bot
    )

    # schedule cannot direct call async functions, if you need to call an async function,
    # call it from the bot event loop (bot.loop.create_task), like in the 'bosta_daily_counter' function below
    schedule.every().day.at("08:30").do(
        bosta_daily_counter, bot
    )

    schedule.every().day.at("03:01").do(
        commemorations, bot
    )

    schedule.every(10).seconds.do(
        check_and_save, bot
    )

    if bot.debug_mode:
        schedule.every(50).seconds.do(
            commemorations, bot
        )
