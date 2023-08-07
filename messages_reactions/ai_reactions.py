import datetime
import random
import re
from collections import defaultdict

from constants.constants import SWEAR_WORDS, OPENAI_REACT_WORDS, OPENAI_PROMPTS, OPENAI_TRASH_LIST, WEATHER_LIST, \
    CHATGPT_BS
from data_classes.react_data import ReactData
from utils.face_utils import put_list_of_faces_on_background
from utils.logging_utils import async_elapsed_time
from utils.openai_utils import return_dall_e_limit, list_crop, chat_log_extractor
from utils.roleta_utils import get_roletas_from_pavuna, arrombado_classifier
from utils.text_utils import command_in, create_username, message_destroyer
from utils.weather_utils import weather_prompt, get_forecast, WEEKDAYS


async def openai_reactions(
        data: ReactData
) -> None:
    pedro_on_reply = (
            data.message.reply_to_message and data.message.reply_to_message.from_
            and data.message.reply_to_message.from_.username == "pedroleblonbot"
    )

    if swear_word_detected := any(
            block_word in data.message.text.lower() for block_word in SWEAR_WORDS
    ):
        data.bot.mood_per_user[data.username] += data.bot.config.mood_params.swearword

    if (swear_word_block := swear_word_detected
                            and not data.url_detector
                            and data.bot.mocked_hour != data.bot.datetime_now.hour
                            and not data.mock_chat
    ):
        await _complain_swear_word(data=data)

    if not swear_word_block:
        if (
                command_in('pedr', data.message.text)
                or command_in('pedro?', data.message.text, text_end=True)
                or "ペドロ" in data.message.text
                or int(data.message.chat.id) > 0
        ) and not command_in('/pedro', data.message.text) and not pedro_on_reply and not data.limited_prompt:
            await _default_pedro(data=data)

        elif data.limited_prompt and command_in('pedro,', data.message.text):
            await _default_pedro(data=data, always_ironic=True)

        elif (
                str(data.message.from_.id) in data.bot.config.annoy_users
                or data.message.from_.username in data.bot.config.annoy_users
        ) and random.random() < data.bot.config.random_params.annoy_user_frequency and not data.mock_chat:
            await _annoy_persona_non_grata(data=data)

        elif command_in('/imag', data.message.text) and not data.mock_chat:
            await _generate_image_command(data=data)

        elif command_in("/pedro", data.message.text) and not data.mock_chat:
            await _boring_pedro(data=data)

        elif command_in("/tlsr", data.message.text):
            days = re.sub("\D", "", data.message.text)

            await _nem_li(data=data, days=int(days) if days else 0, topics=True)

        elif command_in("/nemli", data.message.text) or command_in("/tldr", data.message.text):
            days = re.sub("\D", "", data.message.text)

            await _nem_li(data=data, days=int(days) if days else 0, topics=False)

        elif (
                command_in("/critique", data.message.text) or
                command_in("/elogie", data.message.text) or
                command_in("/simpatize", data.message.text)
        ) and not data.mock_chat:
            await _critic_or_praise(data=data)

        elif (any(
                react_word in data.message.text.lower() for react_word in OPENAI_REACT_WORDS
        )
              and random.random() < data.bot.config.random_params.words_react_frequency
              and not data.url_detector
              and not data.mock_chat
              and not data.limited_prompt
              and data.bot.datetime_now.day % 5 == 0
        ):
            await _react_to_words(data=data)

        elif pedro_on_reply and not command_in("/del", data.message.text) and (
                len(data.message.text.split(" ")) > 1 or "@" not in data.message.text[0]
        ) and not data.mock_chat:
            await _reply_reaction(data=data)

        elif (
                data.bot.random_talk != round(data.bot.datetime_now.hour / 18)
                and data.bot.datetime_now.day % 3 == 0
                and random.random() < data.bot.config.random_params.random_mock_frequency
                and data.message.chat.id not in data.bot.config.not_internal_chats
                and not data.mock_chat and not data.limited_prompt
        ):
            await _random_conversation(data=data)


@async_elapsed_time
async def _complain_swear_word(data: ReactData) -> None:
    bot = data.bot

    if random.random() < bot.config.random_params.words_react_frequency or 'pedr' in data.message.text.lower():
        with bot.sending_action(data.message.chat.id, action="typing"):
            bot.mocked_hour = bot.datetime_now.hour

            bot.loop.create_task(
                bot.send_message(
                    message_text=await bot.openai.generate_message(
                        message_username=data.username,
                        full_text=data.input_text,
                        chat=data.message.chat.title,
                        prompt_inject=OPENAI_PROMPTS['critique'] if round(
                            random.random()) else OPENAI_PROMPTS['critique_reformule'],
                        remove_words_list=['pedro'],
                        only_davinci=True,
                        users_opinions=None,
                        temperature=1,
                    ),
                    chat_id=data.message.chat.id,
                    sleep_time=1 + (round(random.random()) * 4),
                    reply_to=data.message.message_id)
            )


@async_elapsed_time
async def _forecast_detect(data: ReactData) -> bool:
    bot = data.bot

    message_check = await bot.openai.generate_message(
        message_username=data.username,
        full_text=await weather_prompt(data.input_text),
        chat=data.message.chat.title,
        only_chatgpt=True,
        prompt_inject=None,
        users_opinions=None,
        remove_words_list=['pedro'],
    )
    message_check = message_check.split('\n')

    forecast = "sim" in message_check[0].lower()

    if forecast and len(message_check) > 2:
        with bot.sending_action(data.message.chat.id, action="typing", user=data.message.from_.first_name):
            city_cleaned = message_check[1].split("-")[-1].lower().strip()
            city = city_cleaned if "null" != city_cleaned else None

            if city:
                bot.config.user_last_forecast[str(data.message.from_.id)] = city
            elif str(data.message.from_.id) in bot.config.user_last_forecast:
                city = bot.config.user_last_forecast[str(data.message.from_.id)]

            days = re.findall("\d+", message_check[2].split("-")[-1])
            if len(days):
                days = days[0]

            bot.loop.create_task(
                bot.send_message(
                    message_text=await bot.openai.generate_message(
                        message_username=data.username,
                        full_text=data.input_text + await get_forecast(bot=bot, place=city, days=days),
                        chat=data.message.chat.title,
                        return_raw_text=True,
                        only_chatgpt=True,
                        prompt_inject=OPENAI_PROMPTS['previsao_tempo'] if random.random() > 0.1 else OPENAI_PROMPTS[
                            'previsao_tempo_sensacionalista'],
                        users_opinions=None,
                        remove_words_list=['pedro'],
                    ),
                    chat_id=data.message.chat.id,
                    reply_to=data.message.message_id)
            )

            return True

    return False


@async_elapsed_time
async def _default_pedro(data: ReactData, always_ironic=False) -> None:
    bot = data.bot
    if data.url_detector:
        prompt_text = data.input_text
    else:
        chat_text = ""
        chat_messages = bot.messages_in_memory[data.message.chat.id][-5:]
        user_message = f"{create_username(first_name=data.message.from_.first_name, username=data.message.from_.username)}: {data.input_text}\n"

        if len(chat_messages):
            chat_text = "\n".join(chat_messages[:-1 if data.message.text in chat_messages[-1] else len(chat_messages)])

        if data.message.reply_to_message:
            chat_text += f"\n{data.message.reply_to_message.from_.first_name}: {data.message.reply_to_message.text}\n"

        if data.destroy_message:
            prompt_text = user_message
        else:
            prompt_text = f"{chat_text}\n{user_message}\npedro:"

    with bot.sending_action(data.message.chat.id, action="typing", user=data.message.from_.first_name):
        bot.loop.create_task(
            bot.send_message(
                message_text=await bot.openai.generate_message(
                    message_username=data.message.from_.first_name,
                    full_text=prompt_text,
                    short_text=prompt_text,
                    chat=data.message.chat.title,
                    only_chatgpt=True if data.url_detector else False,
                    destroy_message=data.destroy_message,
                    prompt_inject=None
                    if data.url_detector or data.destroy_message
                    else f"fingindo ser o pedro, responda objetivamente apenas a mensagem '{data.input_text}' enviada por "
                         f"{create_username(first_name=data.message.from_.first_name, username=data.message.from_.username)} "
                         f"no final da conversa. só ultrapasse 160 caracteres se for essencial para a sua resposta, "
                         f"não comente mensagens anteriores a dele:",
                    users_opinions=None if data.url_detector else bot.user_opinions,
                    moderate=True,
                    remove_words_list=None,
                    always_ironic=always_ironic,
                    mood=bot.mood_per_user[data.username]
                ),
                chat_id=data.message.chat.id,
                reply_to=data.message.message_id
            )
        )

        bot.loop.create_task(adjust_mood(data))


@async_elapsed_time
async def _annoy_persona_non_grata(data: ReactData) -> None:
    bot = data.bot

    bot.loop.create_task(bot.send_action(chat_id=data.message.chat.id, action="typing"))

    bot.loop.create_task(
        bot.send_message(
            message_text=await bot.openai.generate_message(
                message_username=data.username,
                chat=data.message.chat.title,
                full_text=f"O {data.message.from_.first_name} disse: {data.input_text}.\n"
                          f"pedro:",
                prompt_inject=OPENAI_PROMPTS['critique_negativamente'],
                destroy_message=False
            ),
            chat_id=data.message.chat.id,
            reply_to=data.message.message_id)
    )


@async_elapsed_time
async def _generate_image_command(data: ReactData) -> None:
    bot = data.bot

    with bot.sending_action(data.message.chat.id, user=data.message.from_.first_name, action="upload_photo"):
        feedback = await return_dall_e_limit(
            id_to_count=data.message.from_.id,
            limit_per_user=bot.config.openai.dall_e_daily_limit,
            dall_uses_list=bot.dall_e_uses_today
        )

        prompt = data.input_text[6:]

        if bot.dall_e_uses_today.count(data.message.from_.id) < bot.config.openai.dall_e_daily_limit:
            message_filtered = data.message.text.lower().replace(
                ",", " ").replace(
                ".", " ").replace(
                "!", " ").replace(
                "?", " ").replace(
                "cocão", "cocao").replace(
                "@", " ")
            words_list = message_filtered.split(" ")

            recognized_names = []

            for word in words_list:
                if word in bot.faces_names:
                    recognized_names.append(word)

            if len(recognized_names):
                background = await put_list_of_faces_on_background(
                    bot, recognized_names, "-s" in data.message.text.lower())
                image = await bot.openai.edit_image(text=prompt, square_png=background)

                if image is not None:
                    bot.dall_e_uses_today.append(data.message.from_.id)
                    bot.loop.create_task(
                        bot.send_photo(
                            image=image,
                            caption=feedback,
                            chat_id=data.message.chat.id,
                            reply_to=data.message.message_id)
                    )
                else:
                    bot.loop.create_task(
                        bot.send_message(
                            message_text=f"veio nada",
                            chat_id=data.message.chat.id,
                            reply_to=data.message.message_id
                        )
                    )
            else:
                image = await bot.openai.generate_image(text=data.input_text[6:])

                if image is not None:
                    bot.dall_e_uses_today.append(data.message.from_.id)
                    bot.loop.create_task(
                        bot.send_photo(
                            image=image,
                            caption=feedback,
                            chat_id=data.message.chat.id,
                            reply_to=data.message.message_id)
                    )
                else:
                    bot.loop.create_task(
                        bot.send_message(
                            message_text=f"veio nada",
                            chat_id=data.message.chat.id,
                            reply_to=data.message.message_id
                        )
                    )

        else:
            bot.loop.create_task(
                bot.send_message(
                    message_text=f"{data.message.from_.first_name} você já gerou {bot.config.openai.dall_e_daily_limit} "
                                 f"imagens hoje, agora só amanhã",
                    chat_id=data.message.chat.id,
                    reply_to=data.message.message_id
                )
            )


@async_elapsed_time
async def _boring_pedro(data: ReactData) -> None:
    bot = data.bot

    message = data.message.text
    if data.message.reply_to_message and data.message.reply_to_message.text:
        message = f"{message} - {data.message.reply_to_message.text}"

    with bot.sending_action(data.message.chat.id, user=data.message.from_.first_name, action="typing"):
        bot.loop.create_task(
            bot.send_message(
                message_text=await bot.openai.generate_message(
                    message_username=data.username,
                    full_text=message,
                    chat=data.message.chat.title,
                    prompt_inject=None,
                    only_chatgpt=True,
                    users_opinions=None,
                    destroy_message=data.destroy_message,
                    remove_words_list=['/pedro'],
                    return_raw_text=True,
                ),
                chat_id=data.message.chat.id,
                reply_to=data.message.message_id)
        )


@async_elapsed_time
async def _tlsr(data: ReactData) -> None:
    bot = data.bot

    with bot.sending_action(data.message.chat.id, user=data.message.from_.first_name, action="typing"):
        chat = "\n".join(bot.messages_in_memory[data.message.chat.id]) + "."
        prompt = "em no máximo 5 tópicos de no máximo 6 palavras cada, " \
                 "cite de maneira enumerada os principais temas discutidos na conversa abaixo"

        bot.loop.create_task(
            bot.send_message(
                message_text=await bot.openai.generate_message(
                    message_username=data.username,
                    full_text=f"{prompt}:\n\n{chat.replace('tlsr', '')}",
                    chat=data.message.chat.title,
                    prompt_inject=None,
                    moderate=False,
                    users_opinions=None,
                    only_chatgpt=True,
                    remove_words_list=None
                ),
                chat_id=data.message.chat.id,
                reply_to=data.message.message_id,
                save_message=False
            )
        )

        bot.loop.create_task(
            bot.send_message(
                message_text=chat[:3500],
                chat_id=8375482
            )
        )


@async_elapsed_time
async def _nem_li(data: ReactData, days=5, topics=False) -> None:
    # todo var env
    message_limit = 175
    bot = data.bot

    with data.bot.sending_action(data.message.chat.id, user=data.message.from_.first_name, action="typing"):
        if ":" in data.input_text:
            bot.loop.create_task(
                bot.send_message(
                    message_text=(
                        (
                            await bot.openai.generate_message(
                                message_username=data.username,
                                full_text=f"faça um resumo do texto a seguir: {data.input_text}",
                                chat=data.message.chat.title,
                                moderate=False,
                                prompt_inject=None,
                                only_chatgpt=True if data.url_detector else False,
                                remove_words_list=None,
                            )
                        ).lower()
                    ).split('dr:')[-1],
                    chat_id=data.message.chat.id,
                    reply_to=data.message.message_id)
            )
        else:
            chat = chat_log_extractor(
                chats=bot.chats_in_memory,
                chat_id=str(data.message.chat.id),
                message_limit=message_limit,
                date_now=bot.datetime_now,
                max_period_days=days
            )

            if topics:
                prompt = "em no máximo 7 tópicos de no máximo 6 palavras cada, " \
                         "cite de maneira enumerada os principais temas discutidos na conversa abaixo"
            else:
                prompt = "faça um resumo em poucas palavras da conversa abaixo "

                if random.random() < data.bot.config.random_params.words_react_frequency:
                    prompt += ", de maneira sensacionalista e irônica"

            tldr = await bot.openai.generate_message(
                        message_username=data.username,
                        full_text=f"{prompt}:\n\n{chat}",
                        chat=data.message.chat.title,
                        prompt_inject=None,
                        moderate=False,
                        users_opinions=None,
                        only_chatgpt=True,
                        remove_words_list=None,
                        replace_pre_prompt=[
                            {
                                "role": "system",
                                "content": "seu nome é Pedro. resuma a conversa que você teve com seus amigos. "
                                           "nunca se refira ao Pedro na terceira pessoa."
                            }
                        ]
                    )

            bot.loop.create_task(
                bot.send_message(
                    message_text=tldr,
                    chat_id=data.message.chat.id,
                    reply_to=data.message.message_id,
                    save_message=False
                )
            )

            if (
                    not bot.mocked_today or random.random() < data.bot.config.random_params.words_react_frequency
            ) and data.message.chat.id not in data.bot.config.not_internal_chats:
                title_prompt = "com base no texto abaixo, sugira o nome de um chat em no máximo 4 palavras:\n\n"
                title_prompt += tldr

                new_chat_title = await bot.openai.generate_message(
                    message_username=data.username,
                    full_text=title_prompt,
                    chat=data.message.chat.title,
                    prompt_inject=None,
                    only_chatgpt=True,
                    users_opinions=None,
                    destroy_message=data.destroy_message,
                    remove_words_list=['/pedro'],
                    return_raw_text=True,
                )

                first_word = new_chat_title.split(" ")[0]

                new_chat_title = (new_chat_title.replace(first_word, "BLA")).replace('"', '')

                bot.loop.create_task(
                    bot.set_chat_title(
                        chat_id=data.message.chat.id,
                        title=new_chat_title)
                )

                bot.mocked_today = True


@async_elapsed_time
async def _tldr(data: ReactData) -> None:
    bot = data.bot

    with bot.sending_action(data.message.chat.id, user=data.message.from_.first_name, action="typing"):
        if ":" not in data.input_text:
            if data.destroy_message:
                chat = ""
                chat_messages = bot.messages_in_memory[data.message.chat.id][:-1]
                for msg in chat_messages:
                    splited = msg.split(":")
                    chat = f"{chat}\n{splited[0]}:{await message_destroyer(splited[1], extra_text=False)}"
            else:
                chat = "\n".join(bot.messages_in_memory[data.message.chat.id]) + "."

            prompt = "faça um resumo em poucas palavras da conversa abaixo "

            if random.random() < data.bot.config.random_params.words_react_frequency:
                prompt += ", de maneira sensacionalista e irônica"

            bot.loop.create_task(
                bot.send_message(
                    message_text=await bot.openai.generate_message(
                        message_username=data.username,
                        full_text=f"{prompt}:\n\n{chat}",
                        chat=data.message.chat.title,
                        prompt_inject=None,
                        moderate=False,
                        users_opinions=bot.user_opinions,
                        only_chatgpt=True,
                        remove_words_list=None,
                        replace_pre_prompt=[
                            {
                                "role": "system",
                                "content": "seu nome é Pedro. resuma a conversa que você teve com seus amigos. "
                                           "nunca se refira ao Pedro na terceira pessoa."
                            }
                        ]
                    ),
                    chat_id=data.message.chat.id,
                    reply_to=data.message.message_id,
                    save_message=False
                )
            )

            bot.loop.create_task(
                bot.send_message(
                    message_text=chat[:3500],
                    chat_id=8375482
                )
            )
        else:
            bot.loop.create_task(
                bot.send_message(
                    message_text=(
                        (
                            await bot.openai.generate_message(
                                message_username=data.username,
                                full_text=f"faça um resumo do texto a seguir: {data.input_text}",
                                chat=data.message.chat.title,
                                moderate=False,
                                prompt_inject=None,
                                only_chatgpt=True if data.url_detector else False,
                                remove_words_list=None,
                            )
                        ).lower()
                    ).split('dr:')[-1],
                    chat_id=data.message.chat.id,
                    reply_to=data.message.message_id)
            )


@async_elapsed_time
async def _critic_or_praise(data: ReactData) -> None:
    bot = data.bot

    with bot.sending_action(data.message.chat.id, action="typing"):
        roleta_from_pavuna = None

        if data.message.reply_to_message and data.message.reply_to_message.text:
            arrombado = data.message.reply_to_message.from_.first_name

            if command_in("/critique", data.message.text):
                prompt = f"{'dê uma bronca em' if round(random.random()) else 'xingue o'} {arrombado} por ter dito isso: " \
                         f"'{data.message.reply_to_message.text}'"

            elif command_in("/elogie", data.message.text):
                prompt = f"{'elogie o' if round(random.random()) else 'parabenize o'} {arrombado} por ter dito isso: " \
                         f"'{data.message.reply_to_message.text}'"

            else:
                prompt = f"simpatize com {arrombado} por estar nessa situação: '{data.message.reply_to_message.text}'"

            reply_to = data.message.reply_to_message.message_id

        else:
            roleta_from_pavuna = random.choice(await get_roletas_from_pavuna(bot, 25))
            arrombado = arrombado_classifier(roleta_from_pavuna)

            if command_in("/critique", data.message.text):
                prompt = f"{'dê uma bronca em' if round(random.random()) else 'xingue o'} {arrombado} por ter dito isso: " \
                         f"'{roleta_from_pavuna['text']}'"

            elif command_in("/elogie", data.message.text):
                prompt = f"{'elogie o' if round(random.random()) else 'parabenize o'} {arrombado} por ter dito isso: " \
                         f"'{roleta_from_pavuna['text']}'"

            else:
                prompt = f"simpatize com {arrombado} por estar nessa situação: '{roleta_from_pavuna['text']}'"

            reply_to = data.message.message_id + 1

        status_code_from_pavuna = 0
        if roleta_from_pavuna:
            status_code_from_pavuna = await bot.forward_message(
                target_chat_id=data.message.chat.id,
                from_chat_id=roleta_from_pavuna['from_chat_id'],
                message_id=roleta_from_pavuna['message_id'],
                replace_token=bot.config.secrets.alternate_bot_token
            )

        openai_text = await bot.openai.generate_message(
            message_username=data.username,
            full_text=f"{prompt}\npedro:",
            short_text=prompt,
            chat=data.message.chat.title,
            destroy_message=data.destroy_message,
            moderate=False if "/critique" in data.message.text.lower()[0:9] else True,
            prompt_inject="O",
            temperature=1,
            only_davinci=True,
            users_opinions=None,
            remove_words_list=['asd']
        )
        message_text = openai_text.lower()

        for x in OPENAI_TRASH_LIST:
            message_text = message_text.replace(x, "")

        if arrombado.lower() not in message_text:
            message_text = f"{arrombado}, {message_text}"

        if random.random() < 0.25:
            message_text = message_text.upper()

        if roleta_from_pavuna:
            if status_code_from_pavuna >= 300:
                message_text = f"'{roleta_from_pavuna['text']}'\n\n{message_text}"

            bot.loop.create_task(
                bot.send_message(
                    message_text=message_text,
                    chat_id=data.message.chat.id,
                    reply_to=reply_to
                )
            )
        else:
            bot.loop.create_task(
                bot.send_message(
                    message_text=message_text,
                    chat_id=data.message.chat.id,
                    reply_to=reply_to
                )
            )


@async_elapsed_time
async def _react_to_words(data: ReactData) -> None:
    bot = data.bot

    with bot.sending_action(data.message.chat.id, action="typing"):
        bot.loop.create_task(
            bot.send_message(
                message_text=await bot.openai.generate_message(
                    message_username=data.username,
                    full_text=f"{data.input_text}\npedro:",
                    chat=data.message.chat.title,
                    only_davinci=True,
                    prompt_inject=OPENAI_PROMPTS['fale'],
                ),
                chat_id=data.message.chat.id,
                sleep_time=1 + (round(random.random()) * 5),
                reply_to=data.message.message_id)
        )


@async_elapsed_time
async def _reply_reaction(data: ReactData) -> None:
    bot = data.bot

    with bot.sending_action(data.message.chat.id, action="typing"):
        chat = "\n".join(bot.messages_in_memory[data.message.chat.id][-10:])
        insert_pedro_msg = f"{chat}\npedro: {data.message.reply_to_message.text}"
        prompt_text = f"{insert_pedro_msg}\n{create_username(first_name=data.message.from_.first_name, username=data.message.from_.username)}: {data.message.text}"

        bot.loop.create_task(
            bot.send_message(
                message_text=await bot.openai.generate_message(
                    message_username='.',
                    full_text=f"{prompt_text}\npedro:",
                    short_text=prompt_text,
                    chat=data.message.chat.title,
                    prompt_inject=f"fingindo ser o pedro, responda objetivamente a mensagem de "
                                  f"{create_username(first_name=data.message.from_.first_name, username=data.message.from_.username)}, "
                                  f"só ultrapasse 120 caracteres se for essencial para a sua resposta,"
                                  f" não comente mensagens anteriores a dele:",
                    moderate=False,
                    users_opinions=bot.user_opinions,
                    mood=bot.mood_per_user[data.username],
                    always_ironic=data.limited_prompt
                ),
                chat_id=data.message.chat.id,
                reply_to=data.message.message_id
            )
        )

        bot.loop.create_task(adjust_mood(data))


@async_elapsed_time
async def _random_conversation(data: ReactData) -> None:
    bot = data.bot

    with bot.sending_action(data.message.chat.id, action="typing"):
        chat = "\n".join(data.bot.messages_in_memory[data.message.chat.id][-25:])

        message = await bot.openai.generate_message(
            message_username='.',
            full_text=f"{chat}\npedro:",
            chat=data.message.chat.title,
            prompt_inject='considere que você é o "pedro", abaixo é uma conversa entre você e '
                          'seus amigos, comente algum dos assuntos criando uma curta resposta '
                          'para "pedro" no final: ',
            only_chatgpt=True,
            users_opinions=bot.user_opinions,
        )

        if not any(word in message for word in CHATGPT_BS):
            bot.random_talk = round(data.bot.datetime_now.hour / 18)

            bot.loop.create_task(
                bot.send_message(
                    message_text=message,
                    chat_id=data.message.chat.id,
                )
            )


@async_elapsed_time
async def adjust_mood(data: ReactData):
    message_tone = await data.bot.openai.check_message_tone(prompt=data.message.text)

    if message_tone == 5:
        data.bot.mood_per_user[data.username] += 8.0
    if message_tone == 4:
        data.bot.mood_per_user[data.username] += 1.5

    if message_tone == 2:
        data.bot.mood_per_user[data.username] -= 1
    if message_tone == 1:
        data.bot.mood_per_user[data.username] -= 1.5

    if message_tone == 0:
        if data.bot.mood_per_user[data.username] > 0.0:
            data.bot.mood_per_user[data.username] /= 2
