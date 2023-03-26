import logging

from pedro_leblon import FakePedro, telegram_logging


def daily_routines(bot: FakePedro) -> None:
    try:
        bot.mocked_today = False

        if bot.openai is not None:
            bot.openai.openai_use = 0
            bot.dall_e_uses_today = []

        bot.loop.create_task(
            bot.send_document(
                chat_id=8375482,
                caption=f"Agenda backup {bot.datetime_now}",
                document=open(f'commemorations.json', 'rb').read()
            )
        )
        
        
        bot.loop.create_task(
            bot.send_document(
                chat_id=8375482,
                caption=f"Configs backup {bot.datetime_now}",
                document=open(f'bot_configs.json', 'rb').read()
            )
        )
    except Exception as exc:
        bot.loop.create_task(telegram_logging(exc))
