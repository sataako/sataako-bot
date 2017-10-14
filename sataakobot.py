import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
import argparse


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger('sataakobot')

parser = argparse.ArgumentParser()
parser.add_argument('--deploy-to-heroku',
                    dest='deploy_to_heroku',
                    action='store_true',
                    help='Add this argument to deploy the bot on Heroku. ')
parser.set_defaults(deploy_to_heroku=False)

TELEGRAM_API_TOKEN = os.environ.get('TELEGRAM_API_TOKEN')

if not TELEGRAM_API_TOKEN:
    for key in os.environ:
        print(key)
    raise EnvironmentError('You must set a Telegram API token key environment variable. ')


updater = Updater(token=TELEGRAM_API_TOKEN)
dispatcher = updater.dispatcher


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")


def echo(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Sorry, the application is not yet ready. Shoo! ")


def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")


start_handler = CommandHandler('start', start)
echo_handler = MessageHandler(Filters.text, echo)
unknown_handler = MessageHandler(Filters.command, unknown)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(echo_handler)
dispatcher.add_handler(unknown_handler)


def start_heroku_webhook():
    """ Starts the bot on Heroku using a webhook. """
    global TELEGRAM_API_TOKEN, updater
    heroku_url = os.environ.get('SERVER_URL_HEROKU')
    port = int(os.environ.get('PORT', '5000'))
    updater.start_webhook(listen="0.0.0.0",
                          port=port,
                          url_path=TELEGRAM_API_TOKEN)
    updater.bot.set_webhook(heroku_url + TELEGRAM_API_TOKEN)
    updater.idle()


def start_local_polling():
    """ Starts the bot locally by using polling. """
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    args = parser.parse_args()
    if args.deploy_to_heroku:
        logger.info('Running bot in Heroku using a webhook. ')
        start_heroku_webhook()
    else:
        logger.info('Running bot locally using polling. ')
        start_local_polling()
