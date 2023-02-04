import logging

from pedro_leblon import FakePedro


def daily_routines(bot: FakePedro) -> None:
    try:
        bot.mocked_today = False

        if bot.openai is not None:
            bot.openai.openai_use = 0
            bot.openai.dall_e_use = 0

        bot.loop.create_task(
            bot.send_document(
                chat_id=8375482,
                caption=f"Agenda backup {bot.datetime_now}",
                document=open(f'commemorations.json', 'rb').read()
            )
        )
    except Exception as exc:
        logging.exception(exc)
