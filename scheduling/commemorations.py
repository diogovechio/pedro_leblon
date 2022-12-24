import logging

from pedro_leblon import FakePedro


def commemorations(bot: FakePedro) -> None:
    try:
        today = bot.datetime_now

        day = today.day
        month = today.month

        if day == 25 and month == 12:
            for _id in filter(lambda chat_id: chat_id < 0, bot.allowed_list):
                bot.loop.create_task(
                    bot.send_message(
                        message_text=f"feliz natal",
                        chat_id=_id
                    )
                )

                bot.loop.create_task(
                    bot.send_video(
                        video=open(f'gifs/feliznatal.mp4', 'rb').read(),
                        chat_id=_id
                    )
                )

        if day == 1 and month == 1:
            for _id in filter(lambda chat_id: chat_id < 0, bot.allowed_list):
                bot.loop.create_task(
                    bot.send_message(
                        message_text=f"FELIZ ANO NOVO",
                        chat_id=_id
                    )
                )

                bot.loop.create_task(
                    bot.send_video(
                        video=open(f'gifs/anonovo.mp4', 'rb').read(),
                        chat_id=_id
                    )
                )

    except Exception as exc:
        logging.exception(exc)
