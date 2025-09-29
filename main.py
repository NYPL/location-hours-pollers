import os
import pytz

from datetime import datetime
from lib import LocationsApiClient
from lib.query_helper import build_location_hours_redshift_query, build_update_query
from nypl_py_utils.classes.avro_client import AvroEncoder
from nypl_py_utils.classes.kinesis_client import KinesisClient
from nypl_py_utils.classes.redshift_client import RedshiftClient
from nypl_py_utils.functions.config_helper import load_env_file
from nypl_py_utils.functions.log_helper import create_log

_TIMEZONE = pytz.timezone("US/Eastern")


def main():
    load_env_file(os.environ["ENVIRONMENT"], "config/{}.yaml")
    logger = create_log(__name__)

    if os.environ["MODE"] == "LOCATION_HOURS":
        poll_location_hours(logger)
    elif os.environ["MODE"] == "LOCATION_CLOSURE_ALERT":
        poll_location_closure_alerts(logger)
    else:
        logger.error("Mode not recognized: {}".format(os.environ["MODE"]))
        raise LocationHoursPipelineError(
            "Mode not recognized: {}".format(os.environ["MODE"])
        ) from None


def poll_location_hours(logger):
    today = datetime.now(_TIMEZONE).date()
    weekday = today.strftime("%A")
    locations_api_client = LocationsApiClient()
    avro_encoder = AvroEncoder(os.environ["BASE_SCHEMA_URL"] + "LocationHoursV2")
    kinesis_client = KinesisClient(
        os.environ["HOURS_KINESIS_STREAM_ARN"], int(os.environ["KINESIS_BATCH_SIZE"])
    )

    # Query Redshift for all of the currently stored regular hours for today's
    # day of the week
    redshift_client = RedshiftClient(
        os.environ["REDSHIFT_DB_HOST"],
        os.environ["REDSHIFT_DB_NAME"],
        os.environ["REDSHIFT_DB_USER"],
        os.environ["REDSHIFT_DB_PASSWORD"],
    )
    redshift_table = "location_hours_v2"
    if os.environ["REDSHIFT_DB_NAME"] != "production":
        redshift_table += "_" + os.environ["REDSHIFT_DB_NAME"]
    redshift_client.connect()
    raw_redshift_data = redshift_client.execute_query(
        build_location_hours_redshift_query(redshift_table, weekday)
    )
    redshift_client.close_connection()
    redshift_dict = {row[0]: [row[1], row[2]] for row in raw_redshift_data}

    # Determine the earliest open and latest close or use placeholders if all
    # libraries are closed on that day (Sundays)
    opening_hours = set(
        hours[0] for hours in redshift_dict.values() if hours[0] is not None
    )
    closing_hours = set(
        hours[1] for hours in redshift_dict.values() if hours[1] is not None
    )
    redshift_earliest_open = min(opening_hours) if opening_hours else "25:00"
    redshift_latest_close = max(closing_hours) if closing_hours else "00:00"

    logger.info("Polling Drupal for regular location hours")
    records = []
    for location in locations_api_client.query(query_alerts=False):
        location_id = location["attributes"]["field_ts_location_code"]
        hours_data = next(
            filter(
                lambda daily_hours: daily_hours["day"] == weekday,
                location["attributes"]["location_hours"]["regular_hours"],
            )
        )["hours_data"]
        if len(hours_data) > 1:
            logger.error(
                f"More than one hours range listed for location {location_id}: "
                f"{hours_data}"
            )
            continue
        elif bool(hours_data):
            api_hours = [
                datetime.strptime(hours_data[0]["start"], "%I:%M %p").time(),
                datetime.strptime(hours_data[0]["end"], "%I:%M %p").time(),
            ]
        else:
            api_hours = [None, None]

        redshift_hours = redshift_dict.get(location_id, None)
        if redshift_hours is None and os.environ["ENVIRONMENT"] in {
            "production",
            "test_environment",
        }:
            logger.warning("New location id found: {}".format(location_id))

        # Check today's regular hours in Redshift against today's regular hours
        # in the API and construct a record if they are different
        if redshift_hours != api_hours:
            records.append(
                {
                    "location_id": location_id,
                    "name": location["attributes"]["title"],
                    "weekday": weekday,
                    "regular_open": (
                        None if api_hours[0] is None else api_hours[0].isoformat()
                    ),
                    "regular_close": (
                        None if api_hours[1] is None else api_hours[1].isoformat()
                    ),
                    "date_of_change": today.isoformat(),
                    "is_current": True,
                }
            )
            if api_hours[0] is not None and api_hours[0] < redshift_earliest_open:
                logger.warning(
                    (
                        "Earliest opening time changed: was {old_open} and is "
                        "now {new_open}"
                    ).format(old_open=redshift_earliest_open, new_open=api_hours[0])
                )
            if api_hours[1] is not None and api_hours[1] > redshift_latest_close:
                logger.warning(
                    (
                        "Latest closing time changed: was {old_close} and is now "
                        "{new_close}"
                    ).format(old_close=redshift_latest_close, new_close=api_hours[1])
                )
    encoded_records = avro_encoder.encode_batch(records)
    if os.environ.get("IGNORE_KINESIS", False) != "True":
        kinesis_client.send_records(encoded_records)
    kinesis_client.close()

    if records:
        stale_locations_str = "'" + "','".join(r["location_id"] for r in records) + "'"
        redshift_client.connect()
        redshift_client.execute_transaction(
            [
                (
                    build_update_query(
                        redshift_table, weekday, stale_locations_str, today.isoformat()
                    ),
                    None,
                )
            ]
        )
        redshift_client.close_connection()
    logger.info("Finished location hours poll")


def poll_location_closure_alerts(logger):
    locations_api_client = LocationsApiClient()
    avro_encoder = AvroEncoder(os.environ["BASE_SCHEMA_URL"] + "LocationClosureAlertV2")
    kinesis_client = KinesisClient(
        os.environ["CLOSURE_ALERT_KINESIS_STREAM_ARN"],
        int(os.environ["KINESIS_BATCH_SIZE"]),
    )

    # Query the API for every alert marked as a closure and construct a record
    # for each one
    logger.info("Polling Drupal for location closure alerts")
    records = []
    polling_datetime = datetime.now(_TIMEZONE).isoformat(sep=" ")
    for alert in locations_api_client.query(query_alerts=True):
        if alert["closing_date_start"] != None:
            location_id = alert["location_codes"]
            location_name = alert["location_names"]
            if location_id is None and alert["scope"] != "all":
                # These are centers/divisions and can be ignored
                continue

            if location_id is not None and len(location_id) != 1:
                logger.error(
                    f"More than one location id listed for alert {alert['id']}: "
                    f"{location_id}"
                )
                continue

            if alert["extended"] is None:
                logger.warning(f"NULL 'extended' value for alert {alert['id']}")
            records.append(
                {
                    "alert_id": alert["id"],
                    "location_id": None if location_id is None else location_id[0],
                    "name": None if location_name is None else ", ".join(location_name),
                    "closed_for": alert["message_plain"].strip(),
                    "extended_closing": (
                        None
                        if alert["extended"] is None
                        else alert["extended"].lower() == "true"
                    ),
                    "alert_start": " ".join(alert["closing_date_start"].split("T")),
                    "alert_end": " ".join(alert["closing_date_end"].split("T")),
                    "polling_datetime": polling_datetime,
                }
            )

    # If there are no alerts, still record the datetime of the polling, as it
    # may still be required by the LocationClosureAggregator
    if len(records) == 0:
        records.append(
            {
                "drupal_location_id": "location_closure_alert_poller",
                "polling_datetime": polling_datetime,
            }
        )
    encoded_records = avro_encoder.encode_batch(records)
    if os.environ.get("IGNORE_KINESIS", False) != "True":
        kinesis_client.send_records(encoded_records)
    kinesis_client.close()
    logger.info("Finished location closure alerts poll")


if __name__ == "__main__":
    main()


class LocationHoursPipelineError(Exception):
    def __init__(self, message=None):
        self.message = message
