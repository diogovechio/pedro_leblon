import asyncio

from pedro.main import TelegramBot

if __name__ == '__main__':
    bot = TelegramBot(
        bot_config_file='bot_configs.json',
        secrets_file='secrets.json',
    )

    asyncio.run(
        bot.run()
    )
