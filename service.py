""" Functions for making queries to the Sataako-service and getting message content. """

import requests
import logging
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

SATAAKO_SERVER_URL = os.environ['SATAAKO_SERVER_URL']
CAT_GIF_API_URL = "http://thecatapi.com/api/images/get?format=src&type=gif"


def get_forecast_json(location):
    """ Queries the service for the next moment of rainfall with the given location. """
    longitude, latitude = location['longitude'], location['latitude']
    query = "{}/forecast/{}/{}".format(SATAAKO_SERVER_URL, longitude, latitude)
    try:
        logger.info("Making query to URL %s for rainfall. " % query)
        response = requests.get(query)
        response_code = response.status_code
        logger.info("Response returned with status code %s. " % response_code)
        if response_code == requests.codes.ok:
            return response.json()
        else:
            return []
    except ConnectionError:
        logger.info("Rainfall query to URL %s failed, returning None. " % query)
        return []


def get_rain_map():
    """ Queries the service and returns a rain map image along with a message. """
    logger.info("Calling the service for a new rain map. ")
    try:
        logger.info("Attempting rain map request to service. ")
        response = requests.get(CAT_GIF_API_URL)
        message = "Sorry, we couldn't fetch the rain map but here's a picture of a cat instead! "
        image_url = response.url
    except ConnectionError:
        logger.info("Something went wrong in rain map request, returning None as image instead. ")
        image_url = None
        message = "Something went wrong. "
    return image_url, message
