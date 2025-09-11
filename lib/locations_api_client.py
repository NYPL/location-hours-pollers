import os
import requests
import sys

from nypl_py_utils.functions.log_helper import create_log
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import JSONDecodeError

_ALERTS_URL = "drupal.nypl.org/api/alerts/location"
_LOCATIONS_URL = "drupal.nypl.org/jsonapi/node/library"


class LocationsApiClient:
    """Class for querying the Refinery API for locations data"""

    def __init__(self):
        self.logger = create_log("locations_api_client")

        retry_policy = Retry(
            total=3, backoff_factor=5, status_forcelist=[500, 502, 503, 504]
        )
        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(max_retries=retry_policy))

    def query(self, query_alerts):
        try:
            url = _ALERTS_URL if query_alerts else _LOCATIONS_URL
            if os.environ["ENVIRONMENT"] != "production":
                url = "qa-" + url
            url = "https://" + url
            response = self.session.get(url, params={"page[limit]": 999})
            response.raise_for_status()
        except Exception as e:
            self.logger.error(f"Failed to retrieve response: {e}")
            raise LocationsApiClientError(f"Failed to retrieve response: {e}") from None

        try:
            json_response = response.json()
            return json_response["data"]
        except (JSONDecodeError, KeyError) as e:
            self.logger.error(f"JSON is malformed: {type(e)} {e}")
            raise LocationsApiClientError(f"JSON is malformed: {type(e)} {e}") from None


class LocationsApiClientError(Exception):
    def __init__(self, message=None):
        self.message = message
