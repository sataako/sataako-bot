import logging
from telegram import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler
import os
import argparse
import enum


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('--deploy-local',
                    dest='deploy_local',
                    action='store_true',
                    help='Add this argument to deploy the bot locally using polling.')
parser.set_defaults(deploy_local=False)

TELEGRAM_API_TOKEN = os.environ.get('TELEGRAM_API_TOKEN')

SHOW_MAP = "Show rain map"
UPDATE_LOCATION = "Update location"
SIGN_OUT = "Sign out"


class AppStates(enum.IntEnum):
    """ Enums for the different states of the application. """
    UPDATE_LOCATION = 0
    HANDLE_USER_ACTION = 1
    SIGN_OUT = 2


def start(bot, update):
    keyboard = [[KeyboardButton("Click here to get started", request_location=True)]]
    update.message.reply_text(
        'Hey there and welcome to the Sataako -service! ',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return AppStates.UPDATE_LOCATION


def show_actions_menu(bot, chat_id):
    keyboard = [
        [KeyboardButton(SHOW_MAP)],
        [KeyboardButton(UPDATE_LOCATION, request_location=True)],
        [KeyboardButton(SIGN_OUT)]
    ]
    bot.send_message(
        text="Choose your next action. ",
        chat_id=chat_id,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


def update_location(bot, update):
    logger.info("Updating location for chat with id %s" % update.message.chat.id)
    bot.send_message(text="Your location has been updated!", chat_id=update.message.chat_id)
    show_actions_menu(bot, update.message.chat_id)
    return AppStates.HANDLE_USER_ACTION


def show_rain_map(bot, update):
    logger.info("Getting rain map for chat with id %s. " % update.message.chat.id)
    bot.send_message(text="Here is your rain map! ", chat_id=update.message.chat_id)
    show_actions_menu(bot, update.message.chat_id)
    return AppStates.HANDLE_USER_ACTION


def sign_out(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation. " % user.first_name)
    update.message.reply_text('Hope you enjoyed the service. Bye!',
                              reply_markup=ReplyKeyboardRemove())
    logger.info("Signing user out of application. ")
    return ConversationHandler.END


def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")


def create_bot_updater():
    bot_updater = Updater(token=TELEGRAM_API_TOKEN)
    dispatcher = bot_updater.dispatcher

    start_handler = CommandHandler('start', start)
    unknown_handler = MessageHandler(Filters.command, unknown)
    sign_out_handler = CommandHandler('sign_out', sign_out)

    app_handler = ConversationHandler(
        entry_points=[start_handler],
        states={
            AppStates.UPDATE_LOCATION: [MessageHandler(Filters.location, update_location)],
            AppStates.HANDLE_USER_ACTION: [
                RegexHandler(SHOW_MAP, show_rain_map),
                MessageHandler(Filters.location, update_location),
                RegexHandler(SIGN_OUT, sign_out)
            ]
        },
        fallbacks=[sign_out_handler]
    )

    dispatcher.add_handler(app_handler)
    dispatcher.add_handler(unknown_handler)
    return bot_updater


def start_bot(bot_updater, run_local):
    if run_local:
        logger.info('Running bot locally using polling. ')
        bot_updater.start_polling()
    else:
        logger.info('Running bot in Heroku using a webhook. ')
        heroku_app_name = os.environ.get('APP_NAME_HEROKU')
        port = int(os.environ.get('PORT', '5000'))
        bot_updater.start_webhook(listen="0.0.0.0",
                                  port=port,
                                  url_path=TELEGRAM_API_TOKEN)
        bot_updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(heroku_app_name, TELEGRAM_API_TOKEN))
    bot_updater.idle()


if __name__ == '__main__':
    args = parser.parse_args()
    updater = create_bot_updater()
    start_bot(updater, args.deploy_local)
