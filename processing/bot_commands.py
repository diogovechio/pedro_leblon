import random
from dataclasses import asdict

from data_classes.received_message import TelegramMessage
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
    # elif '/status' in message.text[0:7]:
    #     for key, value in filter(lambda x: x != 'secrets', asdict(bot.config).items()):
    #         print(key, value)
    #     print(message.text)
    elif message.text[0] == '/':
        if bot.reacted_random_command != round(bot.datetime_now.hour / 8):
            bot.loop.create_task(bot.send_message(
                message_text='rs',
                chat_id=message.from_.id,
                reply_to=message.message_id)
            )
            bot.reacted_random_command = round(bot.datetime_now.hour / 8)


async def format_status():
    pass
