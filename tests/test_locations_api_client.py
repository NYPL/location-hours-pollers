import json
import pytest

from lib import LocationsApiClient, LocationsApiClientError
from requests.exceptions import ConnectTimeout


_TEST_API_RESPONSE = {
    "metadata": "test-metadata",
    "data": [{"id": "aa", "name": "library a"}, {"id": "bb", "name": "library b"}],
}


class TestLocationsApiClient:

    def test_query_hours_success(self, requests_mock):
        requests_mock.get(
            "https://qa-drupal.nypl.org/jsonapi/node/library",
            text=json.dumps(_TEST_API_RESPONSE),
        )
        assert LocationsApiClient().query(False) == _TEST_API_RESPONSE["data"]
        assert requests_mock.last_request.qs["page[limit]"] == ["999"]

    def test_query_alerts_success(self, requests_mock):
        requests_mock.get(
            "https://qa-drupal.nypl.org/api/alerts/location",
            text=json.dumps(_TEST_API_RESPONSE),
        )
        assert LocationsApiClient().query(True) == _TEST_API_RESPONSE["data"]
        assert requests_mock.last_request.qs["page[limit]"] == ["999"]

    def test_query_request_error(self, requests_mock):
        requests_mock.get(
            "https://qa-drupal.nypl.org/jsonapi/node/library", exc=ConnectTimeout
        )
        with pytest.raises(LocationsApiClientError):
            LocationsApiClient().query(False)

    def test_query_bad_json_error(self, requests_mock):
        requests_mock.get(
            "https://qa-drupal.nypl.org/jsonapi/node/library", text="bad json"
        )
        with pytest.raises(LocationsApiClientError):
            LocationsApiClient().query(False)

    def test_query_missing_key_error(self, requests_mock):
        requests_mock.get(
            "https://qa-drupal.nypl.org/jsonapi/node/library",
            text=json.dumps({"field": "value"}),
        )
        with pytest.raises(LocationsApiClientError):
            LocationsApiClient().query(False)
