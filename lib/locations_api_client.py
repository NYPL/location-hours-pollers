import os
import requests

from nypl_py_utils.functions.log_helper import create_log
from requests.exceptions import JSONDecodeError, RequestException


class LocationsApiClient:
    """Class for querying the Refinery API for locations data"""

    def __init__(self):
        self.logger = create_log('locations_api_client')
        self.url = os.environ['LOCATIONS_API_URL']

    def query(self):
        self.logger.debug('Querying {}'.format(self.url))
        try:
            response = requests.get(self.url)
            response.raise_for_status()
        except RequestException as e:
            self.logger.error(
                'Failed to retrieve response from {url}: {error}'.format(
                    url=self.url, error=e))
            raise LocationsApiClientError(
                'Failed to retrieve response from {url}: {error}'.format(
                    url=self.url, error=e)) from None

        try:
            json_response = response.json()
            return json_response['locations']
        except (JSONDecodeError, KeyError) as e:
            self.logger.error((
                'JSON retrieved from {url} is malformed: {errorType} '
                '{errorMessage}').format(url=self.url, errorType=type(e),
                                         errorMessage=e))
            raise LocationsApiClientError((
                'JSON retrieved from {url} is malformed: {errorType} '
                '{errorMessage}').format(url=self.url, errorType=type(e),
                                         errorMessage=e)) from None


class LocationsApiClientError(Exception):
    def __init__(self, message=None):
        self.message = message
