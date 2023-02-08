import re
from datetime import datetime
import random
import uuid
import math

from deepface import DeepFace

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
    message_split = message.text.lower().split(' ')

    annual_date_pattern = r'^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[012])'
    once_date_pattern = r'^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[012])\/([2-9][0-9][0-9][0-9])$'

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

    elif '/nomes' in message.text.lower()[0:6]:
        msg = f"eu conheço essas pessoas:\n" + '\n'.join(set(bot.faces_names))

        message_split = message.text.lower().split(" ")

        if len(message_split) == 1:
            bot.loop.create_task(
                bot.send_message(
                    message_text=msg,
                    chat_id=message.chat.id,
                    reply_to=message.message_id
                )
            )
        else:
            for i, name in enumerate(message_split):
                if i == 0:
                    continue
                if name in bot.faces_names:
                    bot.loop.create_task(
                        bot.send_action(
                            chat_id=message.chat.id,
                            action="upload_photo",
                        )
                    )

                    random_file_choice = random.choice(
                        [file_name for file_name in bot.faces_files
                         if name in file_name]
                    )

                    bot.loop.create_task(
                        bot.send_photo(
                            image=open(f"faces/{random_file_choice}", "rb").read(),
                            chat_id=message.chat.id,
                            reply_to=message.message_id)
                    )

                else:
                    bot.loop.create_task(
                        bot.send_message(
                            message_text=f"nao conheço {name}",
                            chat_id=message.chat.id,
                            reply_to=message.message_id
                        )
                    )

    elif '/agendar' in message.text.lower()[0:8]:
        frequency = None

        if re.fullmatch(annual_date_pattern, message_split[-1]):
            frequency = 'annual'
        elif re.fullmatch(once_date_pattern, message_split[-1]):
            frequency = 'once'

        if len(message_split) < 3 or not frequency:
            bot.loop.create_task(
                bot.send_message(
                    message_text=f"exemplo pra agendar:\n"
                                 f"\n<b>Exemplo 1 (anual): </b>/agendar hoje é dia de asd caralho 29/12"
                                 f"\n<b>Exemplo 2 (uma vez): </b>/agendar me lembra de sei la 29/12/2023"
                    ,
                    chat_id=message.chat.id,
                    reply_to=message.message_id,
                    parse_mode="HTML"
                )
            )

        else:
            if frequency == "annual":
                celebration = datetime.strptime(f"{message_split[-1]}/{bot.datetime_now.year}", "%d/%m/%Y")
            else:
                celebration = datetime.strptime(f"{message_split[-1]}", "%d/%m/%Y")

            text = message.text.lower().replace(message_split[-1], '').replace(message_split[0], '').strip()

            bot.commemorations.data.append(
                Commemoration(
                    id=str(uuid.uuid4()),
                    every_year=frequency == 'annual',
                    created_by=message.from_.id,
                    created_at=str(bot.datetime_now),
                    celebrate_at=str(celebration),
                    for_chat=message.chat.id,
                    message=text,
                    anniversary=""
                )
            )

            bot.loop.create_task(
                bot.send_message(
                    message_text=f"<b>{text}</b>\n{message_split[-1]}\nadicionado na agenda",
                    chat_id=message.chat.id,
                    reply_to=message.message_id,
                    parse_mode="HTML"
                )
            )

    elif '/agenda' in message.text.lower()[0:7]:
        agendas = []

        agenda = [
                    f"<b>{entry.id}</b>\n"
                    f"<b>Data:</b> {entry.celebrate_at.day}/{entry.celebrate_at.month}{'/' + str(entry.celebrate_at.year) if not entry.every_year else ''}\n"
                    f"<b>Lembrete:</b> {entry.message if not entry.anniversary else 'Aniversário de ' + entry.anniversary.replace('@', '@ ')}\n"
                    f"<b>Repete todo ano:</b> {entry.every_year}\n"
                    f"<b>{message.from_.first_name} autorizado a deletar:</b> {entry.created_by == message.from_.id}"
                    for entry in bot.commemorations.data
                    if entry.for_chat == message.chat.id
            ]

        message_len = 8
        last_idx = 0
        messages = math.ceil(len(agenda) / message_len)
        for i in range(messages):
            agendas.append('\n\n'.join(agenda[last_idx:message_len + last_idx]))

            last_idx += message_len

        for i, entry in enumerate(agendas):
            bot.loop.create_task(
                bot.send_message(
                    message_text=f"<b>Agendamentos do chat {message.chat.title if message.chat.title else message.chat.username}</b> - {i + 1}/{len(agendas)}\n\n{entry}",
                    chat_id=message.chat.id,
                    parse_mode="HTML"
                )
            )

    elif '/delete' in message.text.lower()[0:7]:
        msg_id = message.text.split(' ')

        if len(msg_id) != 2:
            bot.loop.create_task(
                bot.send_message(
                    message_text=f"para deletar entrada da agenda:\n/delete id",
                    chat_id=message.chat.id,
                    reply_to=message.message_id,
                    parse_mode="HTML"
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
                            reply_to=message.message_id,
                            parse_mode="HTML"
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
                        reply_to=message.message_id,
                        parse_mode="HTML"
                    )
                )

    elif '/aniversario' in message.text.lower()[0:12]:
        if len(message_split) < 3 or not re.fullmatch(annual_date_pattern, message_split[-1]):
            bot.loop.create_task(
                bot.send_message(
                    message_text=f"exemplo pra agendar:\n\n/aniversario @thommazk 29/12",
                    chat_id=message.chat.id,
                    reply_to=message.message_id,
                    parse_mode="HTML"
                )
            )

        else:
            celebration = datetime.strptime(f"{message_split[-1]}/{bot.datetime_now.year}", "%d/%m/%Y")
            anniversary = message.text.lower().replace(message_split[-1], '').replace(message_split[0], '').strip()

            bot.commemorations.data.append(
                Commemoration(
                    id=str(uuid.uuid4()),
                    every_year=True,
                    created_by=message.from_.id,
                    created_at=str(bot.datetime_now),
                    celebrate_at=str(celebration),
                    for_chat=message.chat.id,
                    message="",
                    anniversary=anniversary
                )
            )

            bot.loop.create_task(
                bot.send_message(
                    message_text=f"aniversário de {anniversary} no dia {message_split[-1]} adicionado na agenda",
                    chat_id=message.chat.id,
                    reply_to=message.message_id,
                    parse_mode="HTML"
                )
            )

    elif message.text[0] == '/':
        if bot.reacted_random_command != round(bot.datetime_now.hour / 12):
            bot.loop.create_task(bot.send_message(
                message_text='rs',
                chat_id=message.chat.id)
            )
            bot.reacted_random_command = round(bot.datetime_now.hour / 12)
