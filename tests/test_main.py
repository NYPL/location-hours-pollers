import os
import pytest
import main

from freezegun import freeze_time
from tests.test_helpers import TestHelpers

_TEST_API_RESPONSE = [
    {
        'id': 'liba',
        'name': 'library a',
        'hours': {'regular': [
            {'day': 'Sun.', 'open': '09:00', 'close': '15:00'},
            {'day': 'Mon.', 'open': '10:00', 'close': '16:00'}
        ]},
        '_embedded': {}
    },
    {
        'id': 'libb',
        'name': 'library b',
        'hours': {'regular': [
            {'day': 'Sun.', 'open': '11:00', 'close': '17:00'},
            {'day': 'Mon.', 'open': '12:00', 'close': '18:00'}
        ]},
        '_embedded': {'alerts': [
            {
                'id': '123',
                'closed_for': 'temporary closure 1',
                'extended_closing': None,
                'applies': {
                    'start': '2022-12-31T00:00:00-05:00',
                    'end': '2023-01-31T00:00:00-05:00'
                }
            },
            {
                'id': '456',
                'closed_for': 'temporary closure 2',
                'extended_closing': 'false',
                'applies': {
                    'start': '2023-01-01T00:00:00-05:00',
                    'end': '2023-01-01T12:00:00-05:00'
                }
            },
        ]}
    },
    {
        'id': 'libc',
        'name': 'library c',
        'hours': {'regular': [
            {'day': 'Sun.', 'open': '13:00', 'close': '19:00'},
            {'day': 'Mon.', 'open': '14:00', 'close': '20:00'}
        ]},
        '_embedded': {'alerts': [
            {
                'id': '789',
                'extended_closing': None,
                'applies': {
                    'start': '2022-12-31T00:00:00-05:00',
                    'end': '2023-01-31T00:00:00-05:00'
                }
            },
            {
                'id': '012',
                'extended_closing': 'true',
                'applies': {
                    'start': '2022-12-31T00:00:00-05:00',
                    'end': '2023-02-31T00:00:00-05:00'
                }
            },
        ]}
    },
    {
        'id': 'libd',
        'name': 'library d',
        'hours': {'regular': [
            {'day': 'Sun.', 'open': None, 'close': None},
            {'day': 'Mon.', 'open': None, 'close': None}
        ]},
        '_embedded': {}
    }
]

_TEST_REDSHIFT_RESPONSE = [
    ('liba', '09:00', '10:00'),
    ('libb', '11:00', '17:00'),
    ('libc', '18:00', '19:00'),
    ('libe', '19:00', '20:00')
]

_AVRO_ALERTS_INPUT = [
    {
        'drupal_location_id': 'libb',
        'name': 'library b',
        'alert_id': '123',
        'closed_for': 'temporary closure 1',
        'extended_closing': False,
        'start': '2022-12-31T00:00:00-05:00',
        'end': '2023-01-31T00:00:00-05:00',
        'polling_datetime': '2023-01-01 01:23:45-05:00'
    },
    {
        'drupal_location_id': 'libb',
        'name': 'library b',
        'alert_id': '456',
        'closed_for': 'temporary closure 2',
        'extended_closing': False,
        'start': '2023-01-01T00:00:00-05:00',
        'end': '2023-01-01T12:00:00-05:00',
        'polling_datetime': '2023-01-01 01:23:45-05:00'
    },
    {
        'drupal_location_id': 'libc',
        'name': 'library c',
        'alert_id': '012',
        'closed_for': None,
        'extended_closing': True,
        'start': '2022-12-31T00:00:00-05:00',
        'end': '2023-02-31T00:00:00-05:00',
        'polling_datetime': '2023-01-01 01:23:45-05:00'
    }
]

_AVRO_HOURS_INPUT = [
    {
        'drupal_location_id': 'liba',
        'name': 'library a',
        'weekday': 'Sun',
        'open': '09:00',
        'close': '15:00',
        'date_of_change': '2023-01-01'
    },
    {
        'drupal_location_id': 'libc',
        'name': 'library c',
        'weekday': 'Sun',
        'open': '13:00',
        'close': '19:00',
        'date_of_change': '2023-01-01'
    },
    {
        'drupal_location_id': 'libd',
        'name': 'library d',
        'weekday': 'Sun',
        'open': None,
        'close': None,
        'date_of_change': '2023-01-01'
    }
]


@freeze_time('2023-01-01 01:23:45-05:00')
class TestMain:

    @classmethod
    def setup_class(cls):
        TestHelpers.set_env_vars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clear_env_vars()

    @pytest.fixture
    def test_instance(self, mocker):
        mocker.patch('main.load_env_file')
        mocker.patch('main.create_log')
        mocker.patch('main.build_location_hours_redshift_query',
                     return_value='REDSHIFT QUERY')

        mock_locations_client = mocker.MagicMock()
        mock_locations_client.query.return_value = _TEST_API_RESPONSE
        mocker.patch('main.LocationsApiClient',
                     return_value=mock_locations_client)

    @pytest.fixture
    def mock_avro_encoder(self, mocker):
        mock_avro_encoder = mocker.MagicMock()
        mock_avro_encoder.encode_batch.return_value = [b'1', b'2', b'3']
        mocker.patch('main.AvroEncoder', return_value=mock_avro_encoder)
        return mock_avro_encoder

    @pytest.fixture
    def mock_kinesis_client(self, mocker):
        mock_kinesis_client = mocker.MagicMock()
        mocker.patch('main.KinesisClient', return_value=mock_kinesis_client)
        return mock_kinesis_client

    @pytest.fixture
    def mock_redshift_client(self, mocker):
        mock_redshift_client = mocker.MagicMock()
        mock_redshift_client.execute_query.return_value = \
            _TEST_REDSHIFT_RESPONSE
        mocker.patch('main.RedshiftClient', return_value=mock_redshift_client)
        return mock_redshift_client

    def test_poll_location_closure_alerts(
            self, test_instance, mock_avro_encoder, mock_kinesis_client):
        os.environ['MODE'] = 'LOCATION_CLOSURE_ALERTS'
        main.main()

        mock_avro_encoder.encode_batch.assert_called_once_with(
            _AVRO_ALERTS_INPUT)
        mock_kinesis_client.send_records.assert_called_once_with(
            [b'1', b'2', b'3'])
        mock_kinesis_client.close.assert_called_once()
        del os.environ['MODE']

    def test_poll_location_hours(
        self, test_instance, mock_avro_encoder, mock_kinesis_client,
            mock_redshift_client):
        os.environ['MODE'] = 'LOCATION_HOURS'
        main.main()

        mock_redshift_client.connect.assert_called_once()
        mock_redshift_client.execute_query.assert_called_once_with(
            'REDSHIFT QUERY')
        mock_redshift_client.close_connection.assert_called_once()
        mock_avro_encoder.encode_batch.assert_called_once_with(
            _AVRO_HOURS_INPUT)
        mock_kinesis_client.send_records.assert_called_once_with(
            [b'1', b'2', b'3'])
        mock_kinesis_client.close.assert_called_once()
        del os.environ['MODE']

    def test_unknown_mode(self, test_instance):
        os.environ['MODE'] = 'fake-mode'
        with pytest.raises(main.LocationHoursPipelineError):
            main.main()
        del os.environ['MODE']
