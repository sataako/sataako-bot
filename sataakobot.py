""" Main file for starting the bot from the command line. """

import logging
from telegram import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler
import os
import argparse
import enum
import service

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
RAIN_WARNING_QUERY_INTERVAL = int(os.environ.get('RAIN_WARNING_QUERY_INTERVAL', 120))

SHOW_MAP = "Show rain map"
UPDATE_LOCATION = "Update location"
EXIT_APP = "Exit application"
START_APP = "Start application"


class AppStates(enum.IntEnum):
    """ Enums for the different states of the application. """
    UPDATE_LOCATION = 0
    HANDLE_USER_ACTION = 1
    EXIT_APP = 2


def start(bot, update):
    """ Starts the conversation with a new user and displays a keyboard that requests the location of the user. """
    logger.info("Starting new conversation with chat id %s. " % update.message.chat_id)
    keyboard = [[KeyboardButton("Click here to get started", request_location=True)]]
    update.message.reply_text(
        'Hey there and welcome to the Sataako -service! ',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return AppStates.UPDATE_LOCATION


def show_actions_menu(bot, chat_id):
    """ Displays an actions menu keyboard to the user in the chat. """
    logger.info("Displaying the actions menu in the chat with id %s. " % chat_id)
    keyboard = [
        [KeyboardButton(SHOW_MAP)],
        [KeyboardButton(UPDATE_LOCATION, request_location=True)],
        [KeyboardButton(EXIT_APP)]
    ]
    bot.send_message(
        text="Choose your next action. ",
        chat_id=chat_id,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


def parse_forecast_json(forecast_json):
    """ Parses the forecast JSON and returns a Boolean and a message about rainfall. """
    forecasts = forecast_json.get('forecasts')
    warning = False
    intensity = 0
    rainfall_eta = None
    for forecast in forecasts:
        rain_intensity = forecast.get('rain_intensity')
        if rain_intensity > 0:
            intensity = rain_intensity
            rainfall_eta = forecast.get('time')
            warning = True
            break
    return warning, intensity, rainfall_eta


def callback_rain_warning_to_user(bot, job):
    """ Callback job function for warning the user about rainfall. """
    chat_id = job.context['chat_id']
    location = job.context['location']
    logger.info("Handling rain warning job for chat with id %s. " % chat_id)
    forecast = service.get_forecast_json(location)
    if not forecast:
        return
    warning, intensity, rainfall_eta = parse_forecast_json(forecast)
    if warning:
        logger.info("Sending warning to chat with id %s. " % chat_id)
        message = "Warning! Expecting rainfall at %s. Estimated rainfall intensity is %s. " % (rainfall_eta, intensity)
        bot.send_location(chat_id=chat_id, location=location)
        bot.send_message(chat_id=chat_id, text=message)


def schedule_rain_warning_job(job_queue, user_data, location, chat_id, interval):
    """ Schedules a repeating rain warning job and adds a reference to the job in the user_data dictionary. """
    logger.info("Scheduling a new rain warning job for chat with id %s." % chat_id)
    context = {'location': location, 'chat_id': chat_id}
    rain_warning_job = job_queue.run_repeating(callback_rain_warning_to_user, interval=interval, context=context)
    user_data['job'] = rain_warning_job


def remove_rain_warning_job(user_data):
    """ Schedules the removal of the rain warning job from the user dictionary. """
    logger.info('Removing rain warning job from chat. ')
    if 'job' in user_data:
        logger.info('Job found in user_data, scheduling its removal. ')
        job = user_data['job']
        job.schedule_removal()
    else:
        logger.info('No existing job found in user_data. ')


def update_location(bot, update, job_queue, user_data):
    """ Updates the location of the user and adds a repeating job of warning the user of rainfall. """
    global RAIN_WARNING_QUERY_INTERVAL
    logger.info("Updating location for chat with id %s" % update.message.chat.id)
    location = update.message.location
    chat_id = update.message.chat_id
    remove_rain_warning_job(user_data)
    schedule_rain_warning_job(job_queue, user_data, location, chat_id, interval=RAIN_WARNING_QUERY_INTERVAL)
    update.message.reply_text(text="Your location has been updated!")
    show_actions_menu(bot, update.message.chat_id)
    return AppStates.HANDLE_USER_ACTION


def show_rain_map(bot, update):
    """ Displays a rainfall map in the chat. """
    chat_id = update.message.chat_id
    logger.info("Getting rain map for chat with id %s. " % update.message.chat.id)
    update.message.reply_text(text="Hold on tight, we're fetching the rain map. ")
    bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
    image_url, message = service.get_rain_map()
    bot.send_message(chat_id=chat_id, text=message)
    if image_url:
        bot.send_document(chat_id=chat_id, document=image_url)
    show_actions_menu(bot, update.message.chat_id)
    return AppStates.HANDLE_USER_ACTION


def exit_application(bot, update, user_data):
    """ Exits the conversation with the application and schedules a removal of the warning job. """
    logger.info("Chat with id %s exited the application. " % update.message.chat.id)
    remove_rain_warning_job(user_data)
    user_data.clear()
    keyboard = [[KeyboardButton(START_APP)]]
    update.message.reply_text(
        'Hope you enjoyed the service. '
        'Click the button below to start using the application again. Bye!',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return ConversationHandler.END


def unknown(bot, update):
    """ Function for handling unknown commands in the chat. """
    bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")


def create_bot_updater():
    """ Creates and returns new Updater object for the bot. """
    bot_updater = Updater(token=TELEGRAM_API_TOKEN)
    dispatcher = bot_updater.dispatcher

    start_handler = CommandHandler('start', start)
    unknown_handler = MessageHandler(Filters.command, unknown)
    sign_out_handler = CommandHandler('sign_out', exit_application)

    app_handler = ConversationHandler(
        entry_points=[
            start_handler,
            RegexHandler(START_APP, start)
        ],
        states={
            AppStates.UPDATE_LOCATION: [
                MessageHandler(Filters.location, update_location, pass_job_queue=True, pass_user_data=True)
            ],
            AppStates.HANDLE_USER_ACTION: [
                RegexHandler(SHOW_MAP, show_rain_map),
                MessageHandler(Filters.location, update_location, pass_job_queue=True, pass_user_data=True),
                RegexHandler(EXIT_APP, exit_application, pass_user_data=True)
            ]
        },
        fallbacks=[sign_out_handler]
    )

    dispatcher.add_handler(app_handler)
    dispatcher.add_handler(unknown_handler)
    return bot_updater


def start_bot(bot_updater, run_local):
    """ Starts the given bot Updater either locally using polling or in Heroku using a webhook. """
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
