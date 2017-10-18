""" Functions for making queries to the Sataako-service and getting message content. """

import requests
import logging


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def when_will_it_rain(location):
    """ Queries the service for the next moment of rainfall with the given location. """
    raise NotImplementedError


def get_rain_map():
    """ Queries the service and returns a rain map image along with a message. """
    logger.info("Calling the service for a new rain map. ")
    message = "Sorry, we couldn't fetch the rain map but here's a picture of a cat instead! "
    response = requests.get("http://thecatapi.com/api/images/get?format=src&type=png")
    image_url = response.url
    return image_url, message
