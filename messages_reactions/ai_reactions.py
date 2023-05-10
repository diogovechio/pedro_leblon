import random
import re

from constants.constants import SWEAR_WORDS, OPENAI_REACT_WORDS, OPENAI_PROMPTS, OPENAI_TRASH_LIST, WEATHER_LIST
from data_classes.react_data import ReactData
from utils.face_utils import put_list_of_faces_on_background
from utils.openai_utils import return_dall_e_limit
from utils.roleta_utils import get_roletas_from_pavuna, arrombado_classifier
from utils.text_utils import command_in, get_user_name
from utils.weather_utils import weather_prompt, get_forecast


async def openai_reactions(
        data: ReactData
) -> None:
    pedro_on_reply = (
            data.message.reply_to_message and data.message.reply_to_message.from_
            and data.message.reply_to_message.from_.username == "pedroleblonbot"
    )


    if swear_word_detected := any(
            block_word in data.message.text.lower() for block_word in SWEAR_WORDS
    ) and not data.url_detector and data.bot.mocked_hour != data.bot.datetime_now.hour:
        await _complain_swear_word(data=data)

    if not swear_word_detected:
        if (
                command_in('pedr', data.message.text)
                or command_in('pedro?', data.message.text, text_end=True)
                or "ペドロ" in data.message.text
                or int(data.message.chat.id) > 0
        ) and not command_in('/pedro', data.message.text) and not pedro_on_reply:
            await _regular_pedro_react(data=data)

        elif (
                str(data.message.from_.id) in data.bot.config.annoy_users
                or data.message.from_.username in data.bot.config.annoy_users
        ) and random.random() < data.bot.config.random_params.annoy_user_frequency:
            await _annoy_persona_non_grata(data=data)

        elif command_in('/imag', data.message.text):
            await _generate_image_react(data=data)

        elif command_in("/pedro", data.message.text):
            await _boring_pedro_react(data=data)

        elif command_in("/tldr", data.message.text):
            await _tldr(data=data)

        elif (
                command_in("/critique", data.message.text) or
                command_in("/elogie", data.message.text) or
                command_in("/simpatize", data.message.text)
        ):
            await _critic_or_praise(data=data)

        elif any(
                react_word in data.message.text.lower() for react_word in OPENAI_REACT_WORDS
        ) and random.random() < data.bot.config.random_params.words_react_frequency and not data.url_detector:
            await _react_to_words(data=data)

        elif pedro_on_reply and data.message.text != "/del" and (
            len(data.message.text.split(" ")) > 1 or "@" not in data.message.text[0]
        ):
            await _react_to_be_on_reply(data=data)

        elif (
                data.bot.random_talk != round(data.bot.datetime_now.hour / 8)
                and random.random() < data.bot.config.random_params.random_mock_frequency
                and data.message.chat.id not in data.bot.config.not_internal_chats
        ):
            await _random_conversation_react(data=data)


async def _complain_swear_word(data: ReactData) -> None:
    bot = data.bot

    if random.random() < bot.config.random_params.words_react_frequency or 'pedr' in data.message.text.lower():
        with bot.sending_action(data.message.chat.id, action="typing"):
            bot.mocked_hour = bot.datetime_now.hour

            bot.loop.create_task(
                bot.send_message(
                    message_text=await bot.openai.generate_message(
                        message_username=data.username,
                        message_text=data.input_text,
                        chat=data.message.chat.title,
                        prompt_inject=OPENAI_PROMPTS['critique'] if round(
                            random.random()) else OPENAI_PROMPTS['critique_reformule'],
                        remove_words_list=['pedro'],
                        only_davinci=True,
                        temperature=1.0,
                    ),
                    chat_id=data.message.chat.id,
                    sleep_time=1 + (round(random.random()) * 4),
                    reply_to=data.message.message_id)
            )


async def _forecast_detect(data: ReactData) -> bool:
    bot = data.bot

    message_check = await bot.openai.generate_message(
        message_username=data.username,
        message_text=await weather_prompt(data.input_text),
        chat=data.message.chat.title,
        only_chatgpt=True,
        prompt_inject=None,
        biased=False,
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
                        message_text=data.input_text + await get_forecast(bot=bot, place=city, days=days),
                        chat=data.message.chat.title,
                        return_raw_text=True,
                        only_chatgpt=True,
                        prompt_inject=OPENAI_PROMPTS['previsao_tempo'] if random.random() > 0.1 else OPENAI_PROMPTS[
                            'previsao_tempo_sensacionalista'],
                        biased=False,
                        remove_words_list=['pedro'],
                    ),
                    chat_id=data.message.chat.id,
                    reply_to=data.message.message_id)
            )

            return True

    return False


async def _regular_pedro_react(data: ReactData) -> None:
    bot = data.bot

    if data.url_detector:
        prompt_text = data.input_text
    else:
        chat = "\n".join([message for message in bot.messages_in_memory[data.message.chat.id][-7:-1]])
        prompt_text = f"{chat}\n{get_user_name(data.message)}: {data.input_text}\npedro:"

    with bot.sending_action(data.message.chat.id, action="typing", user=data.message.from_.first_name):
        bot.loop.create_task(
            bot.send_message(
                message_text=await bot.openai.generate_message(
                    message_username=data.message.from_.first_name,
                    message_text=prompt_text,
                    chat=data.message.chat.title,
                    only_chatgpt=True if data.url_detector else False,
                    prompt_inject=None if data.url_detector else OPENAI_PROMPTS['fale'],
                    biased=False if data.url_detector else True,
                    moderate=False,
                    remove_words_list=None,
                ),
                chat_id=data.message.chat.id,
                reply_to=data.message.message_id
            )
        )


async def _annoy_persona_non_grata(data: ReactData) -> None:
    bot = data.bot

    bot.loop.create_task(bot.send_action(chat_id=data.message.chat.id, action="typing"))

    bot.loop.create_task(
        bot.send_message(
            message_text=await bot.openai.generate_message(
                message_username=data.username,
                chat=data.message.chat.title,
                message_text=f"O {data.message.from_.first_name} disse: {data.input_text}.\n"
                             f"pedro:",
                prompt_inject=OPENAI_PROMPTS['critique_negativamente'],
                destroy_message=False
            ),
            chat_id=data.message.chat.id,
            reply_to=data.message.message_id)
    )


async def _generate_image_react(data: ReactData) -> None:
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


async def _boring_pedro_react(data: ReactData) -> None:
    bot = data.bot

    with bot.sending_action(data.message.chat.id, user=data.message.from_.first_name, action="typing"):
        bot.loop.create_task(
            bot.send_message(
                message_text=await bot.openai.generate_message(
                    message_username=data.username,
                    message_text=data.input_text,
                    chat=data.message.chat.title,
                    prompt_inject=None,
                    only_chatgpt=True,
                    biased=False,
                    destroy_message=data.destroy_message,
                    remove_words_list=['/pedro'],
                    return_raw_text=True,
                ),
                chat_id=data.message.chat.id,
                reply_to=data.message.message_id)
        )


async def _tldr(data: ReactData) -> None:
    bot = data.bot

    with bot.sending_action(data.message.chat.id, user=data.message.from_.first_name, action="typing"):
        if ":" not in data.input_text:
            chat = "\n".join(bot.messages_in_memory[data.message.chat.id]) + "."

            bot.loop.create_task(
                bot.send_message(
                    message_text=await bot.openai.generate_message(
                        message_username=data.username,
                        message_text=f"faça um curto resumo dessa conversa entre os amigos:\n{chat}",
                        chat=data.message.chat.title,
                        prompt_inject=None,
                        moderate=False,
                        biased=False,
                        only_chatgpt=True,
                        remove_words_list=None
                    ),
                    chat_id=data.message.chat.id,
                    reply_to=data.message.message_id)
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
                                message_text=f"faça um resumo do texto a seguir: {data.input_text}",
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
            message_text=prompt,
            chat=data.message.chat.title,
            destroy_message=data.destroy_message,
            moderate=False if "/critique" in data.message.text.lower()[0:9] else True,
            prompt_inject="O",
            temperature=1.0,
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


async def _react_to_words(data: ReactData) -> None:
    bot = data.bot

    with bot.sending_action(data.message.chat.id, action="typing"):
        bot.loop.create_task(
            bot.send_message(
                message_text=await bot.openai.generate_message(
                    message_username=data.username,
                    message_text=f"{data.input_text}\npedro:",
                    chat=data.message.chat.title,
                    only_davinci=True,
                    prompt_inject=OPENAI_PROMPTS['fale'],
                ),
                chat_id=data.message.chat.id,
                sleep_time=1 + (round(random.random()) * 5),
                reply_to=data.message.message_id)
        )


async def _react_to_be_on_reply(data: ReactData) -> None:
    bot = data.bot

    with bot.sending_action(data.message.chat.id, action="typing"):
        chat = "\n".join(bot.messages_in_memory[data.message.chat.id][-15:])
        insert_pedro_msg = f"{chat}\npedro: {data.message.reply_to_message.text}"
        prompt_text = f"{insert_pedro_msg}\n{get_user_name(data.message)}: {data.message.text}"

        bot.loop.create_task(
            bot.send_message(
                message_text=await bot.openai.generate_message(
                    message_username='.',
                    message_text=f"{prompt_text}\npedro:",
                    chat=data.message.chat.title,
                    prompt_inject=OPENAI_PROMPTS['fale'],
                    moderate=False,
                    biased=True,
                ),
                chat_id=data.message.chat.id,
            )
        )


async def _random_conversation_react(data: ReactData) -> None:
    bot = data.bot

    bot.random_talk = round(data.bot.datetime_now.hour / 8)

    with bot.sending_action(data.message.chat.id, action="typing"):
        chat = "\n".join(data.bot.messages_in_memory[data.message.chat.id][-25:])
        bot.loop.create_task(
            bot.send_message(
                message_text=await bot.openai.generate_message(
                    message_username='.',
                    message_text=f"{chat}\npedro:",
                    chat=data.message.chat.title,
                    prompt_inject='considere que você é o "pedro", abaixo é uma conversa entre você e '
                                  'seus amigos, comente algum dos assuntos criando uma curta resposta '
                                  'para "pedro" no final: ',
                    only_chatgpt=True,
                    biased=True,
                ),
                chat_id=data.message.chat.id,
            )
        )
