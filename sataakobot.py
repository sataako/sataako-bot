# coding: utf-8
""" Main file for starting the bot from the command line. """

import logging
from json import JSONDecodeError
from telegram import ReplyKeyboardMarkup, KeyboardButton, ChatAction, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler
import os
import argparse
import enum
import service
import pytz
import datetime

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

SHOW_MAP = "Show forecast animation"
UPDATE_LOCATION = "Update location"
EXIT_APP = "Disable rain alerts"
START_APP = "Start application"


class AppStates(enum.IntEnum):
    """ Enums for the different states of the application. """
    ENABLE_ALERTS = 0
    HANDLE_USER_ACTION = 1
    EXIT_APP = 2


def start(bot, update):
    """ Starts the conversation with a new user and displays a keyboard that requests the location of the user. """
    logger.info("Starting new conversation with chat id %s. " % update.message.chat_id)
    keyboard = [[KeyboardButton("Enable rain alerts", request_location=True)]]
    update.message.reply_text(
        'Hey there and welcome to the Sataako -service! ',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return AppStates.ENABLE_ALERTS


def show_actions_menu(bot, chat_id):
    """ Displays an actions menu keyboard to the user in the chat. """
    logger.info("Displaying the actions menu in the chat with id %s. " % chat_id)
    keyboard = [
        [KeyboardButton(SHOW_MAP)],
        [KeyboardButton(UPDATE_LOCATION, request_location=True)],
        [KeyboardButton(EXIT_APP)]
    ]
    bot.send_message(
        text="Psst, I will keep sending you updates about rainfall at your current location. " 
        'If you move to a new location and want to get updates there click "%s" below or click '
        "[here](https://github.com/sataako) to find out more about me!" % (
            UPDATE_LOCATION
        ),
        parse_mode="Markdown",
        chat_id=chat_id,
        disable_web_page_preview=True,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


def parse_forecast_json(forecast_json):
    """ Parses the forecast JSON and returns whether it is currently raining,
    when current state is estimated to end and the expected amount of rain in the next hour. """
    forecasts = forecast_json.get('forecasts')
    is_raining = None
    change_eta = None
    accumulation = forecast_json.get('accumulation', 0.0)
    for forecast in forecasts:
        rain_intensity = forecast.get('rain_intensity')
        if is_raining is None:
            is_raining = rain_intensity > 0
        if is_raining != rain_intensity > 0:
            change_eta = forecast.get('time')
            break
    if change_eta is not None:
        time_format = forecast_json.get('time_format')
        timezone = forecast_json.get('timezone')
        dtime = datetime.datetime.strptime(change_eta, time_format)
        dtime = dtime.replace(tzinfo=pytz.timezone(timezone))
        dtime = dtime.astimezone(pytz.timezone('Europe/Helsinki'))
        change_eta = dtime.strftime("%H:%M")
    return is_raining, change_eta, accumulation


def callback_rain_warning_to_user(bot, job):
    """ Callback job function for warning the user about rainfall. """
    chat_id = job.context['chat_id']
    location = job.context['location']
    warned = job.context.get('warned', False)
    server_was_down = job.context.get('server_was_down', False)
    first_call_to_job = job.context.get('first_call_to_job', True)
    try:
        logger.info("Handling rain warning job for chat with id %s. " % chat_id)
        forecast = service.get_forecast_json(location)
        is_raining, change_eta, accumulation = parse_forecast_json(forecast)
        going_to_rain = (is_raining is False and change_eta is not None)
        if server_was_down:
            bot.send_message(chat_id=chat_id, text="The server is back up again! ")
            job.context['server_was_down'] = False
        if going_to_rain and not warned:
            logger.info("Sending warning to chat with id %s. " % chat_id)
            job.context['warned'] = True
            message = "Warning! Expecting rainfall at %s. " % change_eta
            message += "Estimated rainfall accumulation during the next hour is %.2fmm. " % accumulation
            if not first_call_to_job:
                bot.send_location(chat_id=chat_id, location=location)
            bot.send_message(chat_id=chat_id, text=message)
        if not going_to_rain and first_call_to_job:
            bot.send_message(chat_id=chat_id, text="No rain is forecasted in your area in the next hour. ")
        if is_raining is True:
            logger.info("Setting warned to false to chat with id %s. " % chat_id)
            job.context['warned'] = False
    except (ConnectionError, RuntimeError, JSONDecodeError) as err:
        logger.error("Caught exception of type %s in rain warning job: %s" % (type(err), err))
        job.context['server_was_down'] = True
        if not server_was_down or first_call_to_job:
            bot.send_message(
                text="Sorry, currently I'm not able to produce a forecast. "
                "Don't worry though, I will inform you once the service is back up again! ",
                chat_id=chat_id
            )
    finally:
        job.context['first_call_to_job'] = False


def callback_show_actions_menu_to_user(bot, job):
    chat_id = job.context['chat_id']
    show_actions_menu(bot, chat_id)


def schedule_rain_warning_job(job_queue, user_data, location, chat_id, interval):
    """ Schedules a repeating rain warning job and adds a reference to the job in the user_data dictionary. """
    logger.info("Scheduling a new rain warning job for chat with id %s." % chat_id)
    context = {'location': location, 'chat_id': chat_id}
    rain_warning_job = job_queue.run_repeating(callback_rain_warning_to_user, first=1,
                                               interval=interval, context=context)
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


def enable_alerts(bot, update, job_queue, user_data):
    """ Updates the location of the user and displays the actions menu. """
    location = update.message.location
    chat_id = update.message.chat_id
    logger.info("Enabling alerts for chat with id %s. " % chat_id)
    bot.send_message(text="Hold on while I get a rain update for your current location. ", chat_id=chat_id,
                     reply_markup=ReplyKeyboardRemove())
    register_new_location_and_warning(job_queue, user_data, location, chat_id)
    job_queue.run_once(callback_show_actions_menu_to_user, when=5, context={'chat_id': chat_id})
    return AppStates.HANDLE_USER_ACTION


def register_new_location_and_warning(job_queue, user_data, location, chat_id):
    logger.info("Updating location for chat with id %s" % chat_id)
    remove_rain_warning_job(user_data)
    schedule_rain_warning_job(job_queue, user_data, location, chat_id, interval=RAIN_WARNING_QUERY_INTERVAL)


def update_location(bot, update, job_queue, user_data):
    """ Updates the location of the user and adds a repeating job of warning the user of rainfall. """
    global RAIN_WARNING_QUERY_INTERVAL
    logger.info("Updating location for chat with id %s" % update.message.chat.id)
    location = update.message.location
    chat_id = update.message.chat_id
    register_new_location_and_warning(job_queue, user_data, location, chat_id)
    update.message.reply_text(text="Your location has been updated!")
    return AppStates.HANDLE_USER_ACTION


def show_rain_map(bot, update):
    """ Displays a rainfall map in the chat. """
    chat_id = update.message.chat_id
    logger.info("Getting rain map for chat with id %s. " % update.message.chat.id)
    update.message.reply_text(text="Hold on tight, I'm fetching the forecast animation. ")
    bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
    image_url, message = service.get_rain_map()
    bot.send_message(chat_id=chat_id, text=message)
    if image_url:
        bot.send_document(chat_id=chat_id, document=image_url)
    return AppStates.HANDLE_USER_ACTION


def show_start_application_keyboard(bot, chat_id):
    keyboard = [[KeyboardButton(START_APP)]]
    bot.send_message(
        chat_id=chat_id,
        text="Click the button below to start using the application again.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


def exit_application(bot, update, user_data):
    """ Exits the conversation with the application and schedules a removal of the warning job. """
    logger.info("Chat with id %s exited the application. " % update.message.chat.id)
    remove_rain_warning_job(user_data)
    user_data.clear()
    show_start_application_keyboard(bot, chat_id=update.message.chat_id)
    return ConversationHandler.END


def unknown(bot, update):
    """ Function for handling unknown commands in the chat. """
    bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")


def message_all_conversations_function(updater, conversation_handler):
    """ Creates a SIGTERM handler function that messages all conversations. """
    def sigterm_handler(signal, frame):
        logger.info("Sending message to all conversations about the server going down. ")
        for key in conversation_handler.conversations:
            chat_id, __ = key
            updater.bot.send_message(chat_id=chat_id, text="Sorry, the bot is down for maintenance! ")
            show_start_application_keyboard(updater.bot, chat_id)
    return sigterm_handler


def create_bot_updater():
    """ Creates and returns new Updater object for the bot. """

    start_handler = CommandHandler('start', start)
    unknown_handler = MessageHandler(Filters.command, unknown)
    sign_out_handler = CommandHandler('sign_out', exit_application)

    app_handler = ConversationHandler(
        entry_points=[
            start_handler,
            RegexHandler(START_APP, start)
        ],
        states={
            AppStates.ENABLE_ALERTS: [
                MessageHandler(Filters.location, enable_alerts, pass_job_queue=True, pass_user_data=True)
            ],
            AppStates.HANDLE_USER_ACTION: [
                RegexHandler(SHOW_MAP, show_rain_map),
                MessageHandler(Filters.location, update_location, pass_job_queue=True, pass_user_data=True),
                RegexHandler(EXIT_APP, exit_application, pass_user_data=True)
            ]
        },
        fallbacks=[sign_out_handler]
    )

    bot_updater = Updater(token=TELEGRAM_API_TOKEN)
    dispatcher = bot_updater.dispatcher

    bot_updater.user_sig_handler = message_all_conversations_function(bot_updater, app_handler)

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
