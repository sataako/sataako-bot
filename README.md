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

After this add the required API keys for Telegram and the service to your environment variables.  

### Deployment

Once you have everything installed, you can start the bot by running the command below from the virtual environment. 

```
python sataakobot.py
```


## Built with 

* [pipenv](https://github.com/kennethreitz/pipenv) - Package and virtual environment management. 
* [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) Telegram bot wrapper that was *"simply too good to refuse."*

## License

~ 
