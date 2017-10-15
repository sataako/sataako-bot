# Sataako-bot

This is a Telegram bot that uses the sataako -service to inform users of rainfall in the Helsinki metropolitan area. 

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. 

### Prerequisites

You need to have Python and [pipenv](https://github.com/kennethreitz/pipenv) installed on the machine that you want to run the bot on. In addition you need a [Telegram API key](https://core.telegram.org/bots#6-botfather) for the bot. 

### Installing

Clone this repository, navigate to it on the command line and run the command below. 

```
pipenv install
```
### Setting environment and configuration variables. 

You have to set specific configuration variables that the app will use. 

* `TELEGRAM_API_TOKEN` - The Telegram API token for your bot.
* `APP_NAME_HEROKU` - The name of your Heroku app; only required if you are deploying the bot to Heroku.

### Local deployment

Once you have everything installed and the Telegram API token set the environment variables, you can start running the bot on your local machine. 

Navigate to the directory on your command line and open the virtual environment shell. From that shell run command below. 

```
python sataakobot.py --deploy-local
```

### Heroku deployment

Set the configuration variables mentioned above to your Heroku app and then push the repository to the Heroku remote of your app. 

## Built with 

* [pipenv](https://github.com/kennethreitz/pipenv) - Package and virtual environment management. 
* [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) Telegram bot wrapper that was *"simply too good to refuse."*

## License

~ 
