from pedro_leblon import FakePedro, telegram_logging


def daily_routines(bot: FakePedro) -> None:
    try:
        bot.mocked_today = False

        if bot.openai is not None:
            bot.openai.openai_use = 0
            bot.dall_e_uses_today = []

        bot.loop.create_task(
            bot.send_document(
                chat_id=8375482,
                caption=f"Agenda backup {bot.datetime_now}",
                document=open(f'commemorations.json', 'rb').read()
            )
        )

        bot.loop.create_task(_send_bosta_andre_summary(bot))
        
        bot.loop.create_task(
            bot.send_document(
                chat_id=8375482,
                caption=f"Configs backup {bot.datetime_now}",
                document=open(f'bot_configs.json', 'rb').read()
            )
        )
    except Exception as exc:
        bot.loop.create_task(telegram_logging(exc))


async def _send_bosta_andre_summary(bot: FakePedro):
    andre_chat = "\n".join(bot.messages_in_memory[-942505785])

    await bot.send_message(
        message_text=(
            await bot.openai.generate_message(
                full_text=f"faça um curto resumo da conversa de hoje no chat do andré decaptor:{andre_chat}",
                biased=True,
            )
        ),
        chat_id=-1001369599178,
    )