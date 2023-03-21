import random

from constants.constants import SWEAR_WORDS, OPENAI_REACT_WORDS, OPENAI_PROMPTS, OPENAI_TRASH_LIST
from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro
from utils.face_utils import put_list_of_faces_on_background
from utils.openai_utils import extract_website_paragraph_content, return_dall_e_limit, list_reducer
from utils.roleta_utils import get_roletas_from_pavuna, arrombado_classifier
from utils.text_utils import https_url_extract, command_in


async def openai_reactions(
        bot: FakePedro,
        message: TelegramMessage,
        from_samuel: bool
) -> None:
    input_text = message.text

    username = message.from_.username if message.from_.username else message.from_.first_name
    destroy_message = True if bot.config.block_samuel and from_samuel else False

    if message.reply_to_message and message.reply_to_message.text:
        input_text += ' : ' + message.reply_to_message.text

    if url_detector := await https_url_extract(input_text):
        url_content = await extract_website_paragraph_content(
            url=url_detector,
            session=bot.session
        )

        bot.loop.create_task(
            bot.send_message(
                message_text=url_content,
                chat_id=8375482
            )
        )

        input_text = input_text.replace(url_detector, url_content)

    if swear_word_detected := any(
            block_word in message.text.lower() for block_word in SWEAR_WORDS
    ) and not url_detector and bot.mocked_hour != bot.datetime_now.hour:
        if random.random() < bot.config.random_params.words_react_frequency or 'pedr' in message.text.lower():
            with bot.sending_action(message.chat.id, "typing"):
                bot.mocked_hour = bot.datetime_now.hour

                bot.loop.create_task(
                    bot.send_message(
                        message_text=await bot.openai.generate_message(
                            message_username=username,
                            message_text=input_text,
                            chat=message.chat.title,
                            prompt_inject=OPENAI_PROMPTS['critique'] if round(
                                random.random()) else OPENAI_PROMPTS['critique_reformule'],
                            remove_words_list=['pedro'],
                            temperature=1.0,
                            destroy_message=destroy_message,
                            mock_message=True
                        ),
                        chat_id=message.chat.id,
                        sleep_time=1 + (round(random.random()) * 4),
                        reply_to=message.message_id)
                )

    if not swear_word_detected:
        if (
                command_in('pedr', message.text) or command_in('pedro?', message.text, text_end=True)
        ) and not command_in('/pedro', message.text):
            with bot.sending_action(message.chat.id, "typing"):
                bot.loop.create_task(
                    bot.send_message(
                        message_text=await bot.openai.generate_message(
                            message_username=username,
                            message_text=input_text,
                            chat=message.chat.title,
                            use_chatgpt=True if url_detector else False,
                            prompt_inject=None if url_detector else OPENAI_PROMPTS['responda'],
                            biased=False if url_detector else True,
                            destroy_message=destroy_message,
                            remove_words_list=['pedro'],
                        ),
                        chat_id=message.chat.id,
                        reply_to=message.message_id)
                )

        elif from_samuel and random.random() < bot.config.random_params.mock_samuel_frequency:
            bot.loop.create_task(bot.send_action(chat_id=message.chat.id, action="typing"))

            bot.loop.create_task(
                bot.send_message(
                    message_text=await bot.openai.generate_message(
                        message_username=username,
                        chat=message.chat.title,
                        message_text=f"O samuel disse: {input_text}",
                        prompt_inject=OPENAI_PROMPTS['critique_negativamente'],
                        destroy_message=False
                    ),
                    chat_id=message.chat.id,
                    reply_to=message.message_id)
            )

        elif command_in('/imag', message.text):
            with bot.sending_action(message.chat.id, "upload_photo"):
                feedback = await return_dall_e_limit(
                    id_to_count=message.from_.id,
                    limit_per_user=bot.config.openai.dall_e_daily_limit,
                    dall_uses_list=bot.used_dall_e_today
                )

                prompt = input_text[6:]

                if bot.used_dall_e_today.count(message.from_.id) < bot.config.openai.dall_e_daily_limit:
                    message_filtered = message.text.lower().replace(
                        ",", " ").replace(
                        ".", " ").replace(
                        "!"," ").replace(
                        "?", " ").replace(
                        "cocão", "cocao").replace(
                        "@", " ")
                    words_list = message_filtered.split(" ")
                    recognized_names = []
                    for word in words_list:
                        if word in bot.faces_names:
                            recognized_names.append(word)
                            prompt = prompt.replace(word, "rapaz")
                    if len(recognized_names):
                        sending_message = bot.loop.create_task(bot.send_action(chat_id=message.chat.id, action="upload_photo", repeats=100))

                        background = await put_list_of_faces_on_background(bot, recognized_names, "-s" in message.text.lower())
                        image = await bot.openai.edit_image(text=prompt,square_png=background)

                        if image is not None:
                            bot.used_dall_e_today.append(message.from_.id)
                            bot.loop.create_task(
                                bot.send_photo(
                                    image=image,
                                    caption=feedback,
                                    chat_id=message.chat.id,
                                    reply_to=message.message_id)
                            )
                        else:
                            bot.loop.create_task(
                                bot.send_message(
                                    message_text=f"veio nada",
                                    chat_id=message.chat.id,
                                    reply_to=message.message_id
                                )
                            )

                        sending_message.cancel()
                    else:
                        image = await bot.openai.generate_image(text=input_text[6:])

                        if image is not None:
                            bot.used_dall_e_today.append(message.from_.id)
                            bot.loop.create_task(
                                bot.send_photo(
                                    image=image,
                                    caption=feedback,
                                    chat_id=message.chat.id,
                                    reply_to=message.message_id)
                            )
                        else:
                            bot.loop.create_task(
                                bot.send_message(
                                    message_text=f"veio nada",
                                    chat_id=message.chat.id,
                                    reply_to=message.message_id
                                )
                            )

                else:
                    bot.loop.create_task(
                        bot.send_message(
                            message_text=f"{message.from_.first_name} você já gerou {bot.config.openai.dall_e_daily_limit} imagens hoje, agora só amanhã",
                            chat_id=message.chat.id,
                            reply_to=message.message_id
                        )
                    )

        elif command_in("/pedro", message.text):
            with bot.sending_action(message.chat.id, "typing"):
                bot.loop.create_task(
                    bot.send_message(
                        message_text=await bot.openai.generate_message(
                            message_username=username,
                            message_text=input_text,
                            chat=message.chat.title,
                            prompt_inject=None,
                            use_chatgpt=True,
                            biased=False,
                            destroy_message=destroy_message,
                            remove_words_list=['/pedro'],
                            return_raw_text=True,
                        ),
                        chat_id=message.chat.id,
                        reply_to=message.message_id)
                )

        elif command_in("/tldr", message.text):
            with bot.sending_action(message.chat.id, "typing"):
                if ":" not in input_text:
                   chat = "\n".join(bot.messages_in_memory[message.chat.id]) + "."

                   bot.loop.create_task(
                        bot.send_message(
                            message_text=await bot.openai.generate_message(
                                message_username=username,
                                message_text=f"faça um curto resumo dessa conversa:\n{chat}",
                                chat=message.chat.title,
                                prompt_inject=None,
                                moderate=False,
                                biased=False,
                                use_chatgpt=True,
                                destroy_message=destroy_message,
                                remove_words_list=None
                            ),
                            chat_id=message.chat.id,
                            reply_to=message.message_id)
                    )

                   bot.loop.create_task(
                        bot.send_message(
                            message_text=chat,
                            chat_id=8375482
                        )
                    )
                else:
                    bot.loop.create_task(
                        bot.send_message(
                            message_text=(await bot.openai.generate_message(
                                message_username=username,
                                message_text=f"faça um resumo do texto a seguir: {input_text}",
                                chat=message.chat.title,
                                moderate=False,
                                prompt_inject=None,
                                destroy_message=destroy_message,
                                remove_words_list=None,
                                force_model="text-davinci-003"
                            )).split('tldr:')[-1],
                            chat_id=message.chat.id,
                            reply_to=message.message_id)
                    )

        elif (
                command_in("/critique", message.text) or
                command_in("/elogie", message.text) or
                command_in("/simpatize", message.text)
        ):
            with bot.sending_action(message.chat.id, "typing"):
                roleta_from_pavuna = None

                if message.reply_to_message and message.reply_to_message.text:
                    arrombado = message.reply_to_message.from_.first_name

                    if command_in("/critique", message.text):
                        prompt = f"{'dê uma bronca em' if round(random.random()) else 'xingue o'} {arrombado} por ter dito isso: " \
                                 f"'{message.reply_to_message.text}'"

                    elif command_in("/elogie", message.text):
                        prompt = f"{'elogie o' if round(random.random()) else 'parabenize o'} {arrombado} por ter dito isso: " \
                                 f"'{message.reply_to_message.text}'"

                    else:
                        prompt = f"simpatize com {arrombado} por estar nessa situação: '{message.reply_to_message.text}'"

                    reply_to = message.reply_to_message.message_id

                else:
                    roleta_from_pavuna = random.choice(await get_roletas_from_pavuna(bot, 25))
                    arrombado = arrombado_classifier(roleta_from_pavuna)

                    if command_in("/critique", message.text):
                        prompt = f"{'dê uma bronca em' if round(random.random()) else 'xingue o'} {arrombado} por ter dito isso: " \
                                 f"'{roleta_from_pavuna['text']}'"

                    elif command_in("/elogie", message.text):
                        prompt = f"{'elogie o' if round(random.random()) else 'parabenize o'} {arrombado} por ter dito isso: " \
                                 f"'{roleta_from_pavuna['text']}'"

                    else:
                        prompt = f"simpatize com {arrombado} por estar nessa situação: '{roleta_from_pavuna['text']}'"

                    reply_to = message.message_id + 1

                status_code_from_pavuna = 0
                if roleta_from_pavuna:
                    status_code_from_pavuna = await bot.forward_message(
                        target_chat_id=message.chat.id,
                        from_chat_id=roleta_from_pavuna['from_chat_id'],
                        message_id=roleta_from_pavuna['message_id'],
                        replace_token=bot.config.secrets.alternate_bot_token
                    )

                openai_text = await bot.openai.generate_message(
                    message_username=username,
                    message_text=prompt,
                    chat=message.chat.title,
                    destroy_message=destroy_message,
                    moderate=False if "/critique" in message.text.lower()[0:9] else True,
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
                            chat_id=message.chat.id,
                            reply_to=reply_to
                        )
                    )
                else:
                    bot.loop.create_task(
                        bot.send_message(
                            message_text=message_text,
                            chat_id=message.chat.id,
                            reply_to=reply_to
                        )
                    )

        elif any(
                react_word in message.text.lower() for react_word in OPENAI_REACT_WORDS
        ) and random.random() < bot.config.random_params.words_react_frequency and not url_detector:
            with bot.sending_action(message.chat.id, "typing"):
                bot.loop.create_task(
                    bot.send_message(
                        message_text=await bot.openai.generate_message(
                            message_username=username,
                            message_text=input_text,
                            chat=message.chat.title,
                            prompt_inject=OPENAI_PROMPTS['fale'],
                            destroy_message=destroy_message,
                            mock_message=True
                        ),
                        chat_id=message.chat.id,
                        sleep_time=1 + (round(random.random()) * 5),
                        reply_to=message.message_id)
                )
