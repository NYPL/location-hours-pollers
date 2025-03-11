import json
import os
import pytest

from lib import LocationsApiClient, LocationsApiClientError
from requests.exceptions import ConnectTimeout
from tests.test_helpers import TestHelpers


_TEST_API_RESPONSE = {
    "metadata": "test-metadata",
    "locations": [
        {
            "id": "aa",
            "name": "library a",
            "hours": {
                "regular": [
                    {"day": "Sun.", "open": None, "close": None},
                    {"day": "Mon.", "open": None, "close": None},
                ]
            },
        },
        {
            "id": "bb",
            "name": "library b",
            "hours": {
                "regular": [
                    {"day": "Tue.", "open": "09:00", "close": "17:00"},
                    {"day": "Wed.", "open": "11:00", "close": "18:00"},
                ]
            },
            "_embedded": {
                "alerts": [
                    {
                        "extended_closing": None,
                        "closed_for": "test closure",
                        "applies": {
                            "start": "2023-01-01T00:00:00-05:00",
                            "end": "2030-12-31T00:00:00-05:00",
                        },
                    },
                ]
            },
        },
    ],
}


class TestLocationsApiClient:

    @classmethod
    def setup_class(cls):
        TestHelpers.set_env_vars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clear_env_vars()

    @pytest.fixture
    def test_instance(self):
        return LocationsApiClient()

    def test_query_success(self, test_instance, requests_mock):
        requests_mock.get(
            "https://test_locations_api", text=json.dumps(_TEST_API_RESPONSE)
        )
        assert test_instance.query() == _TEST_API_RESPONSE["locations"]

    def test_query_request_error(self, test_instance, requests_mock):
        os.environ["ENVIRONMENT"] = "production"
        requests_mock.get("https://test_locations_api", exc=ConnectTimeout)
        with pytest.raises(LocationsApiClientError):
            test_instance.query()
        del os.environ["ENVIRONMENT"]

    def test_query_bad_json_error(self, test_instance, requests_mock):
        requests_mock.get("https://test_locations_api", text="bad json")
        with pytest.raises(LocationsApiClientError):
            test_instance.query()

    def test_query_missing_key_error(self, test_instance, requests_mock):
        requests_mock.get(
            "https://test_locations_api", text=json.dumps({"field": "value"})
        )
        with pytest.raises(LocationsApiClientError):
            test_instance.query()
