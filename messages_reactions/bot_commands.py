import re
from asyncio import Task
from dataclasses import asdict
from datetime import datetime
import random
import uuid
import math
import json

from constants.constants import BOLSOFF_LIST, ANNUAL_DATE_PATTERN, ONCE_DATE_PATTERN, PEDRO_MOOD
from data_classes.commemorations import Commemoration
from data_classes.react_data import ReactData
from messages_reactions.utils.date_utils import display_time
from utils.logging_utils import telegram_logging
from utils.text_utils import command_in, create_username


async def bot_commands(
        data: ReactData
) -> None:
    #Todo: organizar a bagunça
    message = data.message
    bot = data.bot
    from_samuel = data.from_samuel

    message_split = message.text.lower().split(' ')

    if command_in('/andrebebado', message.text) and message.from_.username != 'decaptor' and not from_samuel:
        bot.config.random_params.mock_drunk_decaptor_frequency = 1.0
        bot.loop.create_task(bot.send_message(
            message_text='Modo André Bêbado ativado',
            chat_id=message.from_.id)
        )

    elif command_in('/andresobrio', message.text) and message.from_.username != 'decaptor' and not from_samuel:
        bot.config.random_params.mock_drunk_decaptor_frequency = 0.0
        bot.loop.create_task(bot.send_message(
            message_text='Modo André Sóbrio ativado',
            chat_id=message.from_.id)
        )

    elif command_in('/puto', message.text):
        only_instruct = True

        max_mood = len(PEDRO_MOOD)
        actual_mood = round(bot.mood_per_user[data.username])

        if actual_mood < 0:
            actual_mood = 0

        with bot.sending_action(data.message.chat.id, action="typing"):
            prompt = f"considere que você é o pedro.\nem uma escala de 0 a {max_mood}, " \
                     f"onde:\n" \
                     f"0 = extremamente contente, melhores amigos\n" \
                     f"1 = contente" \
                     f"\n...\n" \
                     f"5 = neutro" \
                     f"\n...\n" \
                     f"{max_mood - 1} = puto" \
                     f"\n{max_mood} = extremamente puto:\n"

            if command_in('/putos', message.text):
                persons = ""
                for person, mood in bot.mood_per_user.items():
                    if mood > 3:
                        persons += f"{person.split(' ')[0]}: {int(mood)}\n"

                if persons:
                    prompt += f"temos as seguintes pessoas seguidas da escala do quanto você está puto com elas:\n\n{persons}\n\n" \
                              f"descreva de maneira como você, pedro, se sente com cada uma dessas pessoas, sem dizer o valor da escala. " \
                              f"reclame grosseiramente com aqueles que te deixaram puto, lembrando de alguma situação que essa pessoa fez com você.\npedro:"
                else:
                    prompt = "diga que não está irritado com ninguém.\npedro:"
            else:
                prompt += f"temos o seguinte valor:\n\n{actual_mood}\n\nentão, dentro da escala, " \
                     f"diga para o {data.username} o quanto você " \
                     f"está contente ou puto com ele. sem dizer exatamente os valores e nem revelar a escala." \
                     f"\n{'dê um exemplo de como você se sente com isso.' if round(random.random()) else 'faça uma curta poesia sobre isso.'}\n\n" \
                     f"\npedro:"

            bot.loop.create_task(
                bot.send_message(
                    message_text=(await bot.openai.generate_message(
                        chat=data.message.chat.title,
                        full_text=prompt,
                        temperature=1,
                        only_instruct=only_instruct,
                        moderate=False,
                        users_opinions=None
                    )).lower(),
                    chat_id=message.chat.id,
                    reply_to=message.message_id,
                )
            )

    elif command_in('/data', message.text):
        bot.loop.create_task(
            bot.send_document(
                document=(json.dumps(bot.mood_per_user, indent=4)).encode("utf-8"),
                chat_id=8375482,
                caption="mood"
            )
        )

        bot.loop.create_task(
            bot.send_document(
                document=(json.dumps(bot.user_opinions, indent=4)).encode("utf-8"),
                chat_id=8375482,
                caption="opinions"
            )
        )

    elif command_in('/reload', message.text) and message.from_.username == 'diogovechio':
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

    elif command_in('/stop', message.text):
        for task in bot.messages_tasks[str(message.chat.id)]:
            task: Task
            task.cancel()
            del bot.messages_tasks[task]
        #
        # bot.loop.create_task(
        #     bot.delete_message(
        #         chat_id=message.chat.id,
        #         message_id=message.message_id,
        #     )
        # )
        #
        # bot.loop.create_task(
        #     telegram_logging(
        #         text=f"{message.from_.first_name},{message.text}"
        #     )
        # )

    elif command_in('/bolso', message.text):
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

            bot.loop.create_task(
                bot.send_video(
                    video=open(f'gifs/jair.mp4', 'rb').read(),
                    chat_id=message.chat.id
                )
            )
        else:
            bot.loop.create_task(
                bot.send_message(
                    message_text=f"já fazem {-1 * expiration} que o jair foi embora",
                    chat_id=message.chat.id,
                    reply_to=message.message_id
                )
            )

    elif command_in('/nomes', message.text):
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

    elif command_in('/styles', message.text):
        bot.loop.create_task(
            bot.send_document(
                document=open("styles.pdf", "rb").read(),
                chat_id=message.chat.id,
                reply_to=message.message_id,
            )
        )

    elif command_in('/agendar', message.text):
        frequency = None

        if re.fullmatch(ANNUAL_DATE_PATTERN, message_split[-1]):
            frequency = 'annual'
        elif len(message_split[-1]) == 2 and 0 < int(message_split[-1]) < 32:
            frequency = 'monthly'
        elif re.fullmatch(ONCE_DATE_PATTERN, message_split[-1]):
            frequency = 'once'

        if len(message_split) < 3 or not frequency:
            bot.loop.create_task(
                bot.send_message(
                    message_text=f"exemplo pra agendar:\n"
                                 f"\n<b>Exemplo 1 (anual): </b>/agendar hoje é dia de 29/12"
                                 f"\n<b>Exemplo 2 (uma vez): </b>/agendar me lembra de sei la 29/12/2023"
                                 f"\n<b>Exemplo 3 (mensal): </b>/agendar me lembra disso 05 "
                                 f"(obs.: 31 será sempre considerado o último dia do mês)"
                    ,
                    chat_id=message.chat.id,
                    reply_to=message.message_id,
                    parse_mode="HTML"
                )
            )

        else:
            if frequency == "annual":
                celebration = datetime.strptime(f"{message_split[-1]}/{bot.datetime_now.year}", "%d/%m/%Y")
            elif frequency == "once":
                celebration = datetime.strptime(f"{message_split[-1]}", "%d/%m/%Y")
            elif frequency == "monthly":
                celebration = datetime.strptime(f"{message_split[-1]}/{bot.datetime_now.month}/{bot.datetime_now.year}", "%d/%m/%Y")

            text = message.text.replace(message_split[-1], '').replace(message_split[0], '').strip()

            bot.commemorations.data.append(
                Commemoration(
                    id=str(uuid.uuid4()),
                    frequency=frequency,
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

    elif command_in('/me', message.text):
        user_mood = 0

        for name, mood in bot.mood_per_user.items():
            username = create_username(message.from_.first_name, message.from_.username)
            if username == name:
                user_mood = int(mood)

        bot.loop.create_task(
            bot.send_message(
                message_text=f"*ID:* `{message.from_.id}`\n"
                             f"*Chat ID:* `{message.chat.id}`\n"
                             f"*Meu ódio por você:* `{user_mood}`",
                chat_id=message.chat.id,
                reply_to=message.message_id,
                parse_mode="Markdown"
            )
        )

    elif command_in('/agenda', message.text):
        agendas = []

        agenda = [
                    f"<b>{entry.id}</b>\n"
                    f"<b>Data:</b> {entry.celebrate_at.day}{'/' + str(entry.celebrate_at.month) if not entry.frequency in ['monthly'] else ''}{'/' + str(entry.celebrate_at.year) if not entry.frequency in ['annual', 'monthly'] else ''}\n"
                    f"<b>Lembrete:</b> {entry.message if not entry.anniversary else 'Aniversário de ' + entry.anniversary.replace('@', '@ ')}\n"
                    f"<b>Frequência:</b> {entry.frequency}\n"
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
    elif command_in('/del', message.text) and message.reply_to_message:
        if (
                message.reply_to_message.from_.id == message.from_.id
                or "pedroleblon" in message.reply_to_message.from_.username
                or message.reply_to_message.from_.is_bot
        ):
            bot.loop.create_task(
                bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=message.reply_to_message.message_id
                )
            )

            bot.loop.create_task(
                bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=message.message_id
                )
            )

            bot.loop.create_task(
                telegram_logging(
                    text=f"{message.from_.first_name},{message.text},{message.reply_to_message.text}"
                )
            )
        else:
            with bot.sending_action(data.message.chat.id, action="typing"):
                from_username = create_username(
                    first_name=message.from_.first_name,
                    username=message.from_.username
                )
                reply_username = create_username(
                    first_name=message.reply_to_message.from_.first_name,
                    username=message.reply_to_message.from_.username
                )

                bot.loop.create_task(
                    bot.send_message(
                        message_text=(await bot.openai.generate_message(
                            user_message=from_username + reply_username,
                            chat=data.message.chat.title,
                            full_text=f'critique duramente o '
                                      f'{from_username} '
                                      f'por ter tentado deletar a mensagem "{message.reply_to_message.text}" enviada por'
                                      f" {reply_username}. 'diga que pretende baní-lo do {message.chat.title}.\n\n"
                                      f"pedro:",
                            temperature=1,
                            only_instruct=True,
                            users_opinions=None,
                            prompt_inject="O",
                        )).upper(),
                        chat_id=message.chat.id,
                        reply_to=message.message_id,
                    )
                )

    elif command_in('/delete', message.text):
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

    elif command_in('/aniversario', message.text):
        if len(message_split) < 3 or not re.fullmatch(ANNUAL_DATE_PATTERN, message_split[-1]):
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
