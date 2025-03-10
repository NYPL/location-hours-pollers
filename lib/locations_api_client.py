import os
import requests
import sys

from nypl_py_utils.functions.log_helper import create_log
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import JSONDecodeError, RequestException


class LocationsApiClient:
    """Class for querying the Refinery API for locations data"""

    def __init__(self):
        self.logger = create_log("locations_api_client")
        self.url = os.environ["LOCATIONS_API_URL"]

        retry_policy = Retry(
            total=3, backoff_factor=5, status_forcelist=[500, 502, 503, 504]
        )
        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(max_retries=retry_policy))

    def query(self):
        self.logger.debug("Querying {}".format(self.url))

        try:
            response = self.session.get(self.url)
            response.raise_for_status()
        except RequestException as e:
            if os.environ["ENVIRONMENT"] == "production":
                self.logger.error(
                    "Failed to retrieve response from {url}: {error}".format(
                        url=self.url, error=e
                    )
                )
                raise LocationsApiClientError(
                    "Failed to retrieve response from {url}: {error}".format(
                        url=self.url, error=e
                    )
                ) from None
            else:
                self.logger.info(
                    "Failed to retrieve response from {url}".format(url=self.url)
                )
                sys.exit()

        try:
            json_response = response.json()
            return json_response["locations"]
        except (JSONDecodeError, KeyError) as e:
            self.logger.error(
                (
                    "JSON retrieved from {url} is malformed: {errorType} "
                    "{errorMessage}"
                ).format(url=self.url, errorType=type(e), errorMessage=e)
            )
            raise LocationsApiClientError(
                (
                    "JSON retrieved from {url} is malformed: {errorType} "
                    "{errorMessage}"
                ).format(url=self.url, errorType=type(e), errorMessage=e)
            ) from None


class LocationsApiClientError(Exception):
    def __init__(self, message=None):
        self.message = message
