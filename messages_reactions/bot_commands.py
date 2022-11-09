from datetime import datetime
import random

from constants.constants import BOLSOFF_LIST
from data_classes.received_message import TelegramMessage
from messages_reactions.utils.date_utils import display_time
from pedro_leblon import FakePedro


async def bot_commands(
        bot: FakePedro,
        message: TelegramMessage,
        from_samuel: bool
) -> None:
    if message.text == '/andrebebado' and message.from_.username != 'decaptor' and not from_samuel:
        bot.config.random_params.mock_drunk_decaptor_frequency = 1.0
        bot.loop.create_task(bot.send_message(
            message_text='Modo André Bêbado ativado',
            chat_id=message.from_.id)
        )

    elif message.text == '/andresobrio' and message.from_.username != 'decaptor' and not from_samuel:
        bot.config.random_params.mock_drunk_decaptor_frequency = 0.0
        bot.loop.create_task(bot.send_message(
            message_text='Modo André Sóbrio ativado',
            chat_id=message.from_.id)
        )

    elif message.text == '/reload' and message.from_.username == 'diogovechio':
        await bot.send_message(
            message_text='Recarregando parâmetros',
            chat_id=message.chat.id
        )
        await bot.load_config_params()
        embeddings_count = {key: bot.faces_names.count(key) for key in bot.faces_names}
        bot.loop.create_task(bot.send_message(
            message_text=f"{bot.config.random_params}\n"
                         f"IDS: {bot.allowed_list}\n"
                         f"{bot.config.face_classifier}\n"
                         f"{bot.config.rss_feed}\n\n"
                         f"Total de fotos:\n{embeddings_count}"
            ,
            chat_id=message.chat.id)
        )

    elif '/bolso' in message.text.lower()[0:6]:
        bolso_expires_at = datetime.strptime('1/1/2023', "%m/%d/%Y")
        remaining = bolso_expires_at - bot.datetime_now

        expiration = display_time(int(remaining.total_seconds()))
        bolsoff_message = random.choice(BOLSOFF_LIST)

        if remaining.days >= 0:
            bot.loop.create_task(
                bot.send_message(
                    message_text=f"faltam {expiration} {bolsoff_message}",
                    chat_id=message.chat.id,
                    reply_to=message.message_id
                )
            )

            if 'embora' in bolsoff_message:
                bot.loop.create_task(
                    bot.send_video(
                        video=open(f'gifs/jair.mp4', 'rb').read(),
                        chat_id=message.chat.id
                    )
                )

    elif message.text[0] == '/':
        if bot.reacted_random_command != round(bot.datetime_now.hour / 12):
            bot.loop.create_task(bot.send_message(
                message_text='rs',
                chat_id=message.chat.id)
            )
            bot.reacted_random_command = round(bot.datetime_now.hour / 12)
