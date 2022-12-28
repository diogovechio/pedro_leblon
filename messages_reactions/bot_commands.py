import re
from dataclasses import asdict
from datetime import datetime
import random
import uuid

from constants.constants import BOLSOFF_LIST
from data_classes.commemorations import Commemoration
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

    elif '/agenda' in message.text.lower()[0:7]:
        agenda = '\n\n'.join(
                [
                    f"<b>{entry.id}</b>\n"
                    f"<b>Data:</b> {entry.celebrate_at.day}/{entry.celebrate_at.month}{'/' + str(entry.celebrate_at.year) if not entry.every_year else ''}\n"
                    f"<b>Lembrete</b>: {entry.message if not entry.anniversary else 'Aniversário de ' + entry.anniversary}\n"
                    f"<b>Autorizado a deletar:</b> {entry.created_by == message.from_.id}"
                    for entry in bot.commemorations.data
                    if entry.for_chat == message.chat.id
            ]
        )

        bot.loop.create_task(
            bot.send_message(
                message_text=f"Agenda desse grupo:\n\n{agenda}",
                chat_id=message.chat.id,
                reply_to=message.message_id
            )
        )

    elif '/delete' in message.text.lower()[0:7]:
        msg_id = message.text.split(' ')

        if len(msg_id) != 2:
            bot.loop.create_task(
                bot.send_message(
                    message_text=f"para deletar entrada da agenda:\n/delete id",
                    chat_id=message.chat.id,
                    reply_to=message.message_id
                )
            )
        else:
            found = False

            for idx, entry in enumerate(bot.commemorations.data):
                if found := msg_id[-1] == entry.id and entry.created_by == message.from_.id:
                    bot.loop.create_task(
                        bot.send_message(
                            message_text=f"{msg_id[-1]} deletado da agenda",
                            chat_id=message.chat.id,
                            reply_to=message.message_id
                        )
                    )
                    bot.commemorations.data.pop(idx)

                    break

            if not found:
                bot.loop.create_task(
                    bot.send_message(
                        message_text=f"nao achei {msg_id[-1]}... manda /agenda e copia o id direito "
                                     f"ou vê se você tem permissão pra deletar",
                        chat_id=message.chat.id,
                        reply_to=message.message_id
                    )
                )

    elif '/aniversario' in message.text.lower()[0:12]:
        message_split = message.text.lower().split(' ')
        date_pattern = r'^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[012])'

        if len(message_split) != 3 or not re.fullmatch(date_pattern, message_split[-1]):
            bot.loop.create_task(
                bot.send_message(
                    message_text=f"exemplo pra agendar:\n\n/aniversario @thommazk 29/12",
                    chat_id=message.chat.id,
                    reply_to=message.message_id
                )
            )

        else:
            celebration = datetime.strptime(f"{message_split[-1]}/{bot.datetime_now.year}", "%d/%m/%Y")

            bot.commemorations.data.append(
                Commemoration(
                    id=str(uuid.uuid4()),
                    every_year=True,
                    created_by=message.from_.id,
                    created_at=str(bot.datetime_now),
                    celebrate_at=str(celebration),
                    for_chat=message.chat.id,
                    message="",
                    anniversary=message_split[1]
                )
            )

            bot.loop.create_task(
                bot.send_message(
                    message_text=f"aniversário de {message_split[1]} no dia {message_split[-1]} adicionado na agenda",
                    chat_id=message.chat.id,
                    reply_to=message.message_id
                )
            )

    elif message.text[0] == '/':
        if bot.reacted_random_command != round(bot.datetime_now.hour / 12):
            bot.loop.create_task(bot.send_message(
                message_text='rs',
                chat_id=message.chat.id)
            )
            bot.reacted_random_command = round(bot.datetime_now.hour / 12)
