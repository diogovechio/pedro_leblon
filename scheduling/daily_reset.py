import logging

from pedro_leblon import FakePedro


def daily_reset(bot: FakePedro) -> None:
    try:
        bot.mocked_today = False
    except Exception as exc:
        logging.exception(exc)
