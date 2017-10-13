import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


TELEGRAM_API_KEY = os.environ.get('TELEGRAM_API_KEY')

if not TELEGRAM_API_KEY:
    raise EnvironmentError('You must set a Telegram API key environment variable. ')


updater = Updater(token=TELEGRAM_API_KEY)
dispatcher = updater.dispatcher


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")


def echo(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Sorry, we have no yet implemented any functionality. ")


def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")


start_handler = CommandHandler('start', start)
echo_handler = MessageHandler(Filters.text, echo)
unknown_handler = MessageHandler(Filters.command, unknown)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(echo_handler)
dispatcher.add_handler(unknown_handler)

if __name__ == '__main__':
    updater.start_polling()
    updater.idle()
