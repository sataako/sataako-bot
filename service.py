""" Functions for making queries to the Sataako-service and getting message content. """

from json import JSONDecodeError
import requests
import logging
import os
import time

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

SATAAKO_SERVER_URL = os.environ['SATAAKO_SERVER_URL']
CAT_GIF_API_URL = "http://thecatapi.com/api/images/get?format=src&type=gif"
SATAAKO_RAIN_MAP_URL = "{}/rainmap".format(SATAAKO_SERVER_URL)


def get_forecast_json(location):
    """ Queries the service for the next moment of rainfall with the given location. """
    longitude, latitude = location['longitude'], location['latitude']
    query = "{}/forecast/{}/{}".format(SATAAKO_SERVER_URL, longitude, latitude)
    try:
        logger.info("Making query to URL %s for rainfall. " % query)
        response = requests.get(query)
        response_code = response.status_code
        logger.info("Forecast response returned with status code %s. " % response_code)
        if response_code == requests.codes.ok:
            return response.json()
        else:
            raise RuntimeError('Could not verify that forecast response status was 200 and that content type was JSON.')
    except (ConnectionError, JSONDecodeError):
        logger.info("Rainfall query to URL %s failed, returning None. " % query)
        raise


def content_type_is_gif_image(response):
    """ Returns True if the response object has the content-type of an image and False otherwise. """
    return 'image/gif' in response.headers['content-type']


def rain_map_is_available():
    """ Returns True if a new rain map image is available at the server. """
    try:
        logger.info("Querying the Sataako-service for a rain map. ")
        response = requests.get(SATAAKO_RAIN_MAP_URL)
        return content_type_is_gif_image(response)
    except ConnectionError:
        logger.info("Something went wrong the requests for a rain map. ")
        return False


def get_rain_map_gif_url():
    """ Returns a URL to the rain map if it is available and None otherwise. """
    if rain_map_is_available():
        return SATAAKO_RAIN_MAP_URL+"/{}".format(time.time())
    else:
        return None


def get_new_cat_gif_url():
    """ Returns a URL to a new cat .gif if one can be found and None otherwise. """
    try:
        logger.info("Attempting request to cat image API. ")
        response = requests.get(CAT_GIF_API_URL)
        return response.url
    except ConnectionError:
        logger.info("Something went wrong the cat gif request, returning None. ")
        return None


def get_rain_map():
    """ Queries the service and returns a rain map image along with a message. """
    logger.info("Calling the service for a new rain map. ")
    rain_map_url = get_rain_map_gif_url()
    if rain_map_url:
        logger.info("Rain map URL found. ")
        return rain_map_url, "Here is the current rain map. "
    logger.info("No rain map URL returned, attempting to send a cat image instead. ")
    cat_gif_url = get_new_cat_gif_url()
    if cat_gif_url:
        logger.info("Cat gif URL found. ")
        return cat_gif_url, "Sorry! We couldn't fetch a picture of the rain map but here is a picture of a cat instead."
    logger.info("No cat image URL returned, returning None. ")
    return None, "Sorry, we couldn't fetch the image of the rain map. "
