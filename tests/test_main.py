import logging
import main
import os
import pytest

from datetime import time

_TEST_HOURS_API_RESPONSE = [
    {
        "attributes": {
            "field_ts_location_code": "liba",
            "title": "library a",
            "location_hours": {
                "regular_hours": [
                    {"day": "Sunday", "hours": "9:00 AM-3:00 PM"},
                    {"day": "Monday", "hours": "10:00 AM-4:00 PM"},
                ]
            },
            "other": "other_field",
        },
        "other2": "other_field_2",
    },
    {
        "attributes": {
            "field_ts_location_code": "libb",
            "title": "library b",
            "location_hours": {
                "regular_hours": [
                    {"day": "Sunday", "hours": "11:00 AM-5:00 PM"},
                    {"day": "Monday", "hours": "12:00 PM-6:00 PM"},
                ]
            },
            "other": "other_field",
        },
        "other2": "other_field_2",
    },
    {
        "attributes": {
            "field_ts_location_code": "libc",
            "title": "library c",
            "location_hours": {
                "regular_hours": [
                    {"day": "Sunday", "hours": "1:33 PM-7:44 PM"},
                    {"day": "Monday", "hours": "2:00 PM-8:00 PM"},
                ]
            },
            "other": "other_field",
        },
        "other2": "other_field_2",
    },
    {
        "attributes": {
            "field_ts_location_code": "libd",
            "title": "library d",
            "location_hours": {
                "regular_hours": [
                    {"day": "Sunday", "hours": "Closed"},
                    {"day": "Monday", "hours": "Closed"},
                ]
            },
            "other": "other_field",
        },
        "other2": "other_field_2",
    },
]

_TEST_ALERTS_API_RESPONSE = [
    {
        "id": "123",
        "location_codes": ["libb"],
        "location_names": ["library b"],
        "message_plain": "temporary closure ",
        "extended": "false",
        "closing_date_start": "2022-12-31T00:00:00-05:00",
        "closing_date_end": "2023-01-31T00:00:00-05:00",
    },
    {
        "id": "456",
        "location_codes": ["libc"],
        "location_names": ["library c"],
        "message_plain": " temporary closure 2",
        "extended": "True",
        "closing_date_start": "2022-12-31T00:00:00-05:00",
        "closing_date_end": "2023-01-31T00:00:00-05:00",
    },
    {
        "id": "789",
        "location_codes": ["libd"],
        "location_names": ["library d"],
        "message_plain": "extended closure",
        "extended": "true",
        "closing_date_start": "2022-12-31T00:00:00-05:00",
        "closing_date_end": "2023-02-31T00:00:00-05:00",
    },
    {
        "id": "012",
        "location_codes": None,
        "location_names": None,
        "message_plain": "system closure",
        "extended": "false",
        "closing_date_start": "2023-01-01 00:00:00-05:00",
        "closing_date_end": "2023-01-01 23:59:59-05:00",
    },
]

_TEST_ALERTS_API_WARNING_RESPONSE = [
    {
        "id": "123",
        "location_codes": ["liba"],
        "location_names": ["library a"],
        "message_plain": "not closed",
        "extended": "true",
        "closing_date_start": None,
        "closing_date_end": None,
    },
    {
        "id": "456",
        "location_codes": ["liba", "libaa"],
        "location_names": ["library a"],
        "message_plain": "two codes",
        "extended": "true",
        "closing_date_start": "2022-12-31T00:00:00-05:00",
        "closing_date_end": "2023-01-31T00:00:00-05:00",
    },
    {
        "id": "789",
        "location_codes": ["liba"],
        "location_names": ["library a", "library aa"],
        "message_plain": "two names",
        "extended": "true",
        "closing_date_start": "2022-12-31T00:00:00-05:00",
        "closing_date_end": "2023-01-31T00:00:00-05:00",
    },
    {
        "id": "012",
        "location_codes": ["libd"],
        "location_names": ["library d"],
        "message_plain": "null extended",
        "extended": None,
        "closing_date_start": "2022-12-31T00:00:00-05:00",
        "closing_date_end": "2023-01-31T00:00:00-05:00",
    },
]

_TEST_REDSHIFT_RESPONSE = [
    ("liba", time(9, 0), time(10, 0)),
    ("libb", time(11, 0), time(17, 0)),
    ("libc", time(18, 0), time(19, 0)),
    ("libd", time(19, 0), time(20, 0)),
    ("libe", time(20, 0), time(21, 0)),
]

_AVRO_ALERTS_INPUT = [
    {
        "alert_id": "123",
        "location_id": "libb",
        "name": "library b",
        "closed_for": "temporary closure",
        "extended_closing": False,
        "alert_start": "2022-12-31 00:00:00-05:00",
        "alert_end": "2023-01-31 00:00:00-05:00",
        "polling_datetime": "2023-01-01 01:23:45-05:00",
    },
    {
        "alert_id": "456",
        "location_id": "libc",
        "name": "library c",
        "closed_for": "temporary closure 2",
        "extended_closing": True,
        "alert_start": "2022-12-31 00:00:00-05:00",
        "alert_end": "2023-01-31 00:00:00-05:00",
        "polling_datetime": "2023-01-01 01:23:45-05:00",
    },
    {
        "alert_id": "789",
        "location_id": "libd",
        "name": "library d",
        "closed_for": "extended closure",
        "extended_closing": True,
        "alert_start": "2022-12-31 00:00:00-05:00",
        "alert_end": "2023-02-31 00:00:00-05:00",
        "polling_datetime": "2023-01-01 01:23:45-05:00",
    },
    {
        "alert_id": "012",
        "location_id": None,
        "name": None,
        "closed_for": "system closure",
        "extended_closing": False,
        "alert_start": "2023-01-01 00:00:00-05:00",
        "alert_end": "2023-01-01 23:59:59-05:00",
        "polling_datetime": "2023-01-01 01:23:45-05:00",
    },
]

_AVRO_HOURS_INPUT = [
    {
        "location_id": "liba",
        "name": "library a",
        "weekday": "Sunday",
        "regular_open": "09:00:00",
        "regular_close": "15:00:00",
        "date_of_change": "2023-01-01",
        "is_current": True,
    },
    {
        "location_id": "libc",
        "name": "library c",
        "weekday": "Sunday",
        "regular_open": "13:33:00",
        "regular_close": "19:44:00",
        "date_of_change": "2023-01-01",
        "is_current": True,
    },
    {
        "location_id": "libd",
        "name": "library d",
        "weekday": "Sunday",
        "regular_open": None,
        "regular_close": None,
        "date_of_change": "2023-01-01",
        "is_current": True,
    },
]


class TestMain:

    @pytest.fixture
    def test_instance(self, mocker):
        mocker.patch("main.load_env_file")
        mocker.patch(
            "main.build_location_hours_redshift_query", return_value="REDSHIFT QUERY"
        )

    @pytest.fixture
    def mock_avro_encoder(self, mocker):
        mock_avro_encoder = mocker.MagicMock()
        mock_avro_encoder.encode_batch.return_value = [b"1", b"2", b"3", b"4"]
        mocker.patch("main.AvroEncoder", return_value=mock_avro_encoder)
        return mock_avro_encoder

    @pytest.fixture
    def mock_kinesis_client(self, mocker):
        mock_kinesis_client = mocker.MagicMock()
        mocker.patch("main.KinesisClient", return_value=mock_kinesis_client)
        return mock_kinesis_client

    @pytest.fixture
    def mock_redshift_client(self, mocker):
        mock_redshift_client = mocker.MagicMock()
        mock_redshift_client.execute_query.return_value = _TEST_REDSHIFT_RESPONSE
        mocker.patch("main.RedshiftClient", return_value=mock_redshift_client)
        return mock_redshift_client

    def test_poll_location_closure_alerts(
        self, test_instance, mock_avro_encoder, mock_kinesis_client, mocker, caplog
    ):
        os.environ["MODE"] = "LOCATION_CLOSURE_ALERT"
        mock_locations_client = mocker.MagicMock()
        mock_locations_client.query.return_value = _TEST_ALERTS_API_RESPONSE
        mocker.patch("main.LocationsApiClient", return_value=mock_locations_client)

        with caplog.at_level(logging.WARNING):
            main.main()

        assert caplog.text == ""
        mock_avro_encoder.encode_batch.assert_called_once_with(_AVRO_ALERTS_INPUT)
        mock_kinesis_client.send_records.assert_called_once_with(
            [b"1", b"2", b"3", b"4"]
        )
        mock_kinesis_client.close.assert_called_once()
        del os.environ["MODE"]

    def test_poll_location_closure_alerts_with_warnings(
        self, test_instance, mock_avro_encoder, mock_kinesis_client, mocker, caplog
    ):
        os.environ["MODE"] = "LOCATION_CLOSURE_ALERT"
        mock_locations_client = mocker.MagicMock()
        mock_locations_client.query.return_value = _TEST_ALERTS_API_WARNING_RESPONSE
        mocker.patch("main.LocationsApiClient", return_value=mock_locations_client)

        with caplog.at_level(logging.WARNING):
            main.main()

        assert (
            "More than one location id listed for alert 456: ['liba', 'libaa']"
            in caplog.text
        )
        assert (
            "More than one location name listed for alert 789: ['library a', "
            "'library aa']" in caplog.text
        )
        assert "NULL 'extended' value for alert 012" in caplog.text
        mock_avro_encoder.encode_batch.assert_called_once_with(
            [
                {
                    "alert_id": "012",
                    "location_id": "libd",
                    "name": "library d",
                    "closed_for": "null extended",
                    "extended_closing": None,
                    "alert_start": "2022-12-31 00:00:00-05:00",
                    "alert_end": "2023-01-31 00:00:00-05:00",
                    "polling_datetime": "2023-01-01 01:23:45-05:00",
                },
            ]
        )
        del os.environ["MODE"]

    def test_poll_location_closure_alerts_empty(
        self, test_instance, mock_avro_encoder, mock_kinesis_client, mocker, caplog
    ):
        os.environ["MODE"] = "LOCATION_CLOSURE_ALERT"
        mock_locations_client = mocker.MagicMock()
        mock_locations_client.query.return_value = _TEST_ALERTS_API_WARNING_RESPONSE[:1]
        mocker.patch("main.LocationsApiClient", return_value=mock_locations_client)

        with caplog.at_level(logging.WARNING):
            main.main()

        assert caplog.text == ""
        mock_avro_encoder.encode_batch.assert_called_once_with(
            [
                {
                    "drupal_location_id": "location_closure_alert_poller",
                    "polling_datetime": "2023-01-01 01:23:45-05:00",
                }
            ]
        )
        del os.environ["MODE"]

    def test_poll_location_hours(
        self,
        test_instance,
        mock_avro_encoder,
        mock_kinesis_client,
        mock_redshift_client,
        mocker,
        caplog,
    ):
        os.environ["MODE"] = "LOCATION_HOURS"
        mock_locations_client = mocker.MagicMock()
        mock_locations_client.query.return_value = _TEST_HOURS_API_RESPONSE
        mocker.patch("main.LocationsApiClient", return_value=mock_locations_client)
        mock_update_builder = mocker.patch(
            "main.build_update_query", return_value="UPDATE QUERY"
        )

        with caplog.at_level(logging.WARNING):
            main.main()

        assert caplog.text == ""
        assert mock_redshift_client.connect.call_count == 2
        mock_redshift_client.execute_query.assert_called_once_with("REDSHIFT QUERY")
        assert mock_redshift_client.close_connection.call_count == 2
        mock_update_builder.assert_called_once_with(
            "location_hours_v2_test_redshift_name", "Sunday", "'liba','libc','libd'"
        )
        mock_redshift_client.execute_transaction.assert_called_once_with(
            [("UPDATE QUERY", None)]
        )
        mock_avro_encoder.encode_batch.assert_called_once_with(_AVRO_HOURS_INPUT)
        mock_kinesis_client.send_records.assert_called_once_with(
            [b"1", b"2", b"3", b"4"]
        )
        mock_kinesis_client.close.assert_called_once()
        del os.environ["MODE"]

    def test_poll_location_hours_with_warnings(
        self,
        test_instance,
        mock_avro_encoder,
        mock_kinesis_client,
        mock_redshift_client,
        mocker,
        caplog,
    ):
        os.environ["MODE"] = "LOCATION_HOURS"
        mock_locations_client = mocker.MagicMock()
        mock_locations_client.query.return_value = [
            {
                "attributes": {
                    "field_ts_location_code": "libf",
                    "title": "library f",
                    "location_hours": {
                        "regular_hours": [
                            {"day": "Sunday", "hours": "8:00 AM-10:00 PM"}
                        ]
                    },
                }
            }
        ]
        mocker.patch("main.LocationsApiClient", return_value=mock_locations_client)

        with caplog.at_level(logging.WARNING):
            main.main()

        assert "New location id found: libf" in caplog.text
        assert (
            "Earliest opening time changed: was 09:00:00 and is now 08:00:00"
            in caplog.text
        )
        assert (
            "Latest closing time changed: was 21:00:00 and is now 22:00:00"
            in caplog.text
        )
        mock_avro_encoder.encode_batch.assert_called_once_with(
            [
                {
                    "location_id": "libf",
                    "name": "library f",
                    "weekday": "Sunday",
                    "regular_open": "08:00:00",
                    "regular_close": "22:00:00",
                    "date_of_change": "2023-01-01",
                    "is_current": True,
                }
            ]
        )
        del os.environ["MODE"]

    def test_poll_location_hours_all_closed(
        self, test_instance, mock_avro_encoder, mock_kinesis_client, mocker
    ):
        os.environ["MODE"] = "LOCATION_HOURS"
        mock_locations_client = mocker.MagicMock()
        mock_locations_client.query.return_value = _TEST_HOURS_API_RESPONSE[-1:]
        mocker.patch("main.LocationsApiClient", return_value=mock_locations_client)

        mock_redshift_client = mocker.MagicMock()
        mock_redshift_client.execute_query.return_value = [("libd", None, None)]
        mocker.patch("main.RedshiftClient", return_value=mock_redshift_client)

        main.main()

        mock_avro_encoder.encode_batch.assert_called_once_with([])
        mock_redshift_client.connect.assert_called_once()
        mock_redshift_client.execute_transaction.assert_not_called()
        del os.environ["MODE"]

    def test_unknown_mode(self, test_instance):
        os.environ["MODE"] = "fake-mode"
        with pytest.raises(main.LocationHoursPipelineError):
            main.main()
        del os.environ["MODE"]
