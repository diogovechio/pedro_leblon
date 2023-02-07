import random

from constants.constants import OPENAI_BLOCK_WORDS, OPENAI_REACT_WORDS, OPENAI_PROMPTS, OPENAI_TRASH_LIST
from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro
from utils.face_utils import put_list_of_faces_on_background
from utils.openai_utils import extract_website_paragraph_content, return_dall_e_limit
from utils.roleta_utils import get_roletas_from_pavuna, arrombado_classifier
from utils.text_utils import https_url_extract


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

    if bot.openai.openai_use < bot.openai.davinci_daily_limit:
        if url_detector := await https_url_extract(input_text):
            url_content = await extract_website_paragraph_content(
                url=url_detector,
                session=bot.session
            )
            input_text = input_text.replace(url_detector, url_content)

    if openai_block_word_detected := any(
            block_word in message.text.lower() for block_word in OPENAI_BLOCK_WORDS
    ):
        if random.random() < bot.config.random_params.words_react_frequency or 'pedr' in message.text.lower():
            bot.loop.create_task(bot.send_action(chat_id=message.chat.id, action="typing"))

            bot.loop.create_task(
                bot.send_message(
                    message_text=await bot.openai.generate_message(
                        message_username=message.from_.username,
                        message_text=input_text,
                        chat=message.chat.title,
                        prompt_inject=OPENAI_PROMPTS['critique'] if round(
                            random.random()) else OPENAI_PROMPTS['critique_reformule'],
                        remove_words_list=['pedro'],
                        sentences=2,
                        tokens=165,
                        temperature=1.0,
                        destroy_message=destroy_message,
                        mock_message=True
                    ),
                    chat_id=message.chat.id,
                    sleep_time=1 + (round(random.random()) * 4),
                    reply_to=message.message_id)
            )

    if not openai_block_word_detected:
        if 'pedr' in message.text.lower()[0:5] and "/pedro" not in message.text.lower()[0:6]:
            bot.loop.create_task(bot.send_action(chat_id=message.chat.id, action="typing"))

            bot.loop.create_task(
                bot.send_message(
                    message_text=await bot.openai.generate_message(
                        message_username=message.from_.username,
                        message_text=input_text,
                        chat=message.chat.title,
                        prompt_inject=OPENAI_PROMPTS[
                            'responda'] if '?' in message.text.lower() else OPENAI_PROMPTS['fale'],
                        destroy_message=destroy_message
                    ),
                    chat_id=message.chat.id,
                    reply_to=message.message_id)
            )

        elif from_samuel and (
                random.random() < bot.config.random_params.mock_samuel_frequency or
                any(
                    react_word in message.text.lower() for react_word in OPENAI_REACT_WORDS
                )
        ):
            bot.loop.create_task(bot.send_action(chat_id=message.chat.id, action="typing"))

            bot.loop.create_task(
                bot.send_message(
                    message_text=await bot.openai.generate_message(
                        message_username=message.from_.username,
                        chat=message.chat.title,
                        message_text=f"O samuel disse: {input_text}",
                        prompt_inject=OPENAI_PROMPTS['critique_negativamente'],
                        destroy_message=False
                    ),
                    chat_id=message.chat.id,
                    reply_to=message.message_id)
            )

        elif "/imag" in message.text.lower()[0:5]:
            limit_per_user = round(bot.config.openai.dall_e_daily_limit / 10)

            feedback = await return_dall_e_limit(
                _id=message.from_.id,
                limit_per_user=limit_per_user,
                used_dall_e_today=bot.used_dall_e_today
            )

            prompt = input_text[6:]

            if bot.used_dall_e_today.count(message.from_.id) < limit_per_user:
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
                    bot.loop.create_task(bot.send_action(chat_id=message.chat.id, action="upload_photo"))

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
                else:
                    bot.loop.create_task(bot.send_action(chat_id=message.chat.id, action="upload_photo"))

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
                        bot.loop.create_task(bot.send_action(chat_id=message.chat.id,action="typing"))

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
                        message_text=f"{message.from_.first_name} você já gerou {limit_per_user} imagens hoje, agora só amanhã",
                        chat_id=message.chat.id,
                        reply_to=message.message_id
                    )
                )

        elif "/pedro" in message.text.lower()[0:6]:
            bot.loop.create_task(bot.send_action(chat_id=message.chat.id, action="typing"))

            bot.loop.create_task(
                bot.send_message(
                    message_text=await bot.openai.generate_message(
                        message_username=message.from_.username,
                        message_text=input_text,
                        chat=message.chat.title,
                        prompt_inject=None,
                        biased=False,
                        destroy_message=destroy_message,
                        remove_words_list=['/pedro'],
                        return_raw_text=True
                    ),
                    chat_id=message.chat.id,
                    reply_to=message.message_id)
            )

        elif "/tldr" in message.text.lower()[0:5]:
            if " " not in message.text or ":" not in message.text:
                chat = "\n".join(bot.messages_in_memory[message.chat.id])
                bot.loop.create_task(bot.send_action(chat_id=message.chat.id, action="typing"))

                bot.loop.create_task(
                    bot.send_message(
                        message_text=await bot.openai.generate_message(
                            message_username=message.from_.username,
                            message_text=f"faça um curto resumo dessa conversa:\n{chat}",
                            chat=message.chat.title,
                            prompt_inject=None,
                            biased=False,
                            destroy_message=destroy_message,
                            remove_words_list=None
                        ),
                        chat_id=message.chat.id,
                        reply_to=message.message_id)
                )
            else:
                bot.loop.create_task(bot.send_action(chat_id=message.chat.id, action="typing"))

                bot.loop.create_task(
                    bot.send_message(
                        message_text=await bot.openai.generate_message(
                            message_username=message.from_.username,
                            message_text=f"faça um resumo do texto a seguir: {input_text}",
                            chat=message.chat.title,
                            prompt_inject=None,
                            destroy_message=destroy_message,
                            remove_words_list=None
                        ),
                        chat_id=message.chat.id,
                        reply_to=message.message_id)
                )

        elif "/critique" in message.text.lower()[0:9] or "/elogie" in message.text.lower()[0:7]:
            roleta_from_pavuna = None
            critic = "/critique" in message.text.lower()[0:9]

            if message.reply_to_message and message.reply_to_message.text:
                arrombado = message.reply_to_message.from_.first_name
                if critic:
                    prompt = f"{'dê uma bronca em' if round(random.random()) else 'xingue o'} {arrombado} por ter dito isso: " \
                             f"'{message.reply_to_message.text}'"
                else:
                    prompt = f"{'elogie o' if round(random.random()) else 'parabenize o'} {arrombado} por ter dito isso: " \
                             f"'{message.reply_to_message.text}'"
                reply_to = message.reply_to_message.message_id
            else:
                roleta_from_pavuna = random.choice(await get_roletas_from_pavuna(bot, 25))
                arrombado = arrombado_classifier(roleta_from_pavuna)
                if critic:
                    prompt = f"{'dê uma bronca em' if round(random.random()) else 'xingue o'} {arrombado} por ter dito isso: " \
                             f"'{roleta_from_pavuna['text']}'"
                else:
                    prompt = f"{'elogie o' if round(random.random()) else 'parabenize o'} {arrombado} por ter dito isso: " \
                             f"'{roleta_from_pavuna['text']}'"
                reply_to = message.message_id + 1

            status_code_from_pavuna = 0
            if roleta_from_pavuna:
                status_code_from_pavuna = await bot.forward_message(
                    target_chat_id=message.chat.id,
                    from_chat_id=roleta_from_pavuna['from_chat_id'],
                    message_id=roleta_from_pavuna['message_id'],
                    replace_token=bot.config.secrets.alternate_bot_token
                )

            bot.loop.create_task(bot.send_action(chat_id=message.chat.id, action="typing"))

            openai_text = await bot.openai.generate_message(
                message_username=message.from_.username,
                message_text=prompt,
                chat=message.chat.title,
                destroy_message=destroy_message,
                prompt_inject="O",
                temperature=1.0,
                sentences=2,
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

        elif (
                len(message.text) >= 25 and True
                and message.chat.id not in bot.config.not_internal_chats
                and not bot.mocked_today
        ):
            roleta_list = (await get_roletas_from_pavuna(bot, 25))
            prompt = f"assumindo que alguém disse: '{random.choice(roleta_list)['text']}' e o {username} disse: '{message.text}', {'continue o assunto' if round(random.random()) else 'puxe outro assunto com base no que está sendo conversado'}."
            bot.loop.create_task(bot.send_action(chat_id=message.chat.id, action="typing"))

            bot.loop.create_task(
                bot.send_message(
                    message_text=(
                        await bot.openai.generate_message(
                            message_text=prompt,
                            chat=message.chat.title,
                            temperature=1.0,
                            sentences=2
                        )
                    ),
                    chat_id=message.chat.id,
                    sleep_time=1 + (round(random.random()) * 5),
                    reply_to=message.message_id
                )
            )

            bot.mocked_today = True

        elif any(
                react_word in message.text.lower() for react_word in OPENAI_REACT_WORDS
        ) and random.random() < bot.config.random_params.words_react_frequency:
            bot.loop.create_task(bot.send_action(chat_id=message.chat.id, action="typing"))

            bot.loop.create_task(
                bot.send_message(
                    message_text=await bot.openai.generate_message(
                        message_username=message.from_.username,
                        message_text=input_text,
                        chat=message.chat.title,
                        prompt_inject=OPENAI_PROMPTS['fale'],
                        sentences=1,
                        tokens=150,
                        destroy_message=destroy_message,
                        mock_message=True
                    ),
                    chat_id=message.chat.id,
                    sleep_time=1 + (round(random.random()) * 5),
                    reply_to=message.message_id)
            )