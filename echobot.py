import logging
import telegram
import enum
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

TOKEN = """463554964:AAG7XBJSQU4-KHKpMpQUBIEgQSsRq3mYFy8"""

updater = Updater(token=TOKEN)
dispatcher = updater.dispatcher

location_keyboard = telegram.KeyboardButton(text="Send location", request_location=True)
reply_kb_markup = telegram.ReplyKeyboardMarkup([[location_keyboard]])


class States(enum.Enum):
    QUERIED, LOCATION = range(2)


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")


def echo(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text=update.message.text)


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
