import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
import argparse


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger('sataakobot')

parser = argparse.ArgumentParser()
parser.add_argument('--deploy-local',
                    dest='deploy_local',
                    action='store_true',
                    help='Add this argument to deploy the bot locally using polling. . ')
parser.set_defaults(deploy_local=False)

TELEGRAM_API_TOKEN = os.environ.get('TELEGRAM_API_TOKEN')

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
    heroku_app_name = os.environ.get('HEROKU_APP_NAME')
    port = int(os.environ.get('PORT', '5000'))
    updater.start_webhook(listen="0.0.0.0",
                          port=port,
                          url_path=TELEGRAM_API_TOKEN)
    updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(heroku_app_name, TELEGRAM_API_TOKEN))
    updater.idle()


def start_local_polling():
    """ Starts the bot locally by using polling. """
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    args = parser.parse_args()
    if args.deploy_local:
        logger.info('Running bot locally using polling. ')
        start_local_polling()
    else:
        logger.info('Running bot in Heroku using a webhook. ')
        start_heroku_webhook()
