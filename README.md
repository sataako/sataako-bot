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

After installing the application you have to set the configuration variables in the `.env.example` file. Once you have configured the variables, rename the file to `.env` - note that only some of the variables are required for local deployment. 

### Local deployment

Once you have everything installed and the Telegram API token set in the `.env` file, you can start running the bot on your local machine. 

Navigate to the directory on your command line and open the virtual environment shell. From that shell run command below. 

```
python sataakobot.py --deploy-local
```

### Heroku deployment

In order to deploy the bot to Heroku you have to also add the name of your Heroku application in the `.env` file. After this you should be able to deploy the bot by pushing the repository to the Heroku remote. 


## Built with 

* [pipenv](https://github.com/kennethreitz/pipenv) - Package and virtual environment management. 
* [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) Telegram bot wrapper that was *"simply too good to refuse."*

## License

~ 
