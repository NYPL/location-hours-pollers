import os
import pytz

from datetime import datetime
from lib import LocationsApiClient
from lib.query_helper import build_location_hours_redshift_query
from nypl_py_utils.classes.avro_encoder import AvroEncoder
from nypl_py_utils.classes.kinesis_client import KinesisClient
from nypl_py_utils.classes.redshift_client import RedshiftClient
from nypl_py_utils.functions.config_helper import load_env_file
from nypl_py_utils.functions.log_helper import create_log


_TIMEZONE = pytz.timezone('US/Eastern')
_WEEKDAY_MAP = {0: 'Mon.', 1: 'Tue.', 2: 'Wed.',
                3: 'Thu.', 4: 'Fri.', 5: 'Sat.', 6: 'Sun.'}


def main():
    load_env_file(os.environ['ENVIRONMENT'], 'config/{}.yaml')
    logger = create_log(__name__)

    if os.environ['MODE'] == 'LOCATION_HOURS':
        poll_location_hours(logger)
    elif os.environ['MODE'] == 'LOCATION_CLOSURE_ALERT':
        poll_location_closure_alerts(logger)
    else:
        logger.error('Mode not recognized: {}'.format(os.environ['MODE']))
        raise LocationHoursPipelineError(
            'Mode not recognized: {}'.format(os.environ['MODE'])) from None


def poll_location_hours(logger):
    locations_api_client = LocationsApiClient()
    avro_encoder = AvroEncoder(os.environ['BASE_SCHEMA_URL'] + 'LocationHours')
    kinesis_client = KinesisClient(os.environ['HOURS_KINESIS_STREAM_ARN'],
                                   int(os.environ['KINESIS_BATCH_SIZE']))

    # Get today's date and day of the week. The Refinery weekday contains a
    # period and the Redshift weekday does not.
    today = datetime.now(_TIMEZONE).date()
    api_weekday = _WEEKDAY_MAP[today.weekday()]
    redshift_weekday = api_weekday.rstrip('.')

    # Query Redshift for all of the currently stored regular hours for today's
    # day of the week
    redshift_client = RedshiftClient(
        os.environ['REDSHIFT_DB_HOST'],
        os.environ['REDSHIFT_DB_NAME'],
        os.environ['REDSHIFT_DB_USER'],
        os.environ['REDSHIFT_DB_PASSWORD'])
    redshift_client.connect()
    raw_redshift_data = redshift_client.execute_query(
        build_location_hours_redshift_query(redshift_weekday))
    redshift_client.close_connection()
    redshift_dict = {row[0]: (str(row[1]), str(row[2]))
                     for row in raw_redshift_data}

    logger.info('Polling Refinery for regular location hours')
    records = []
    for location in locations_api_client.query():
        api_hours = next(filter(
            lambda daily_hours: daily_hours['day'] == api_weekday,
            location['hours']['regular']))
        redshift_hours = redshift_dict.get(location['id'], None)
        if redshift_hours is None:
            logger.warning('New location id found: {}'.format(location['id']))

        # Check today's regular hours in Redshift against today's regular hours
        # in the API and construct a record if they are different
        if (redshift_hours is None
            or redshift_hours[0] != api_hours['open']
                or redshift_hours[1] != api_hours['close']):
            records.append({
                'drupal_location_id': location['id'],
                'name': location['name'],
                'weekday': redshift_weekday,
                'open': api_hours['open'],
                'close': api_hours['close'],
                'date_of_change': str(today)})
    encoded_records = avro_encoder.encode_batch(records)
    kinesis_client.send_records(encoded_records)
    kinesis_client.close()
    logger.info('Finished location hours poll')


def poll_location_closure_alerts(logger):
    locations_api_client = LocationsApiClient()
    avro_encoder = AvroEncoder(
        os.environ['BASE_SCHEMA_URL'] + 'LocationClosureAlert')
    kinesis_client = KinesisClient(
        os.environ['CLOSURE_ALERT_KINESIS_STREAM_ARN'],
        int(os.environ['KINESIS_BATCH_SIZE']))

    # Query the API for every alert marked as a closure and construct a record
    # for each one
    logger.info('Polling Refinery for location closure alerts')
    records = []
    polling_datetime = datetime.now(_TIMEZONE)
    for location in locations_api_client.query():
        for alert in location['_embedded'].get('alerts', []):
            if alert['extended_closing'] == 'true' or 'closed_for' in alert:
                records.append({
                    'drupal_location_id': location['id'],
                    'name': location['name'],
                    'alert_id': alert['id'],
                    'closed_for': alert.get('closed_for', None),
                    'extended_closing': alert['extended_closing'] == 'true',
                    'start': alert['applies']['start'],
                    'end': alert['applies']['end'],
                    'polling_datetime': str(polling_datetime)})

    # If there are no alerts, still record the datetime of the polling, as it
    # may still be required by the LocationClosureAggregator
    if len(records) == 0:
        records.append({'drupal_location_id': 'location_closure_alert_poller',
                       'polling_datetime': str(polling_datetime)})
    encoded_records = avro_encoder.encode_batch(records)
    kinesis_client.send_records(encoded_records)
    kinesis_client.close()
    logger.info('Finished location closure alerts poll')


if __name__ == '__main__':
    main()


class LocationHoursPipelineError(Exception):
    def __init__(self, message=None):
        self.message = message
