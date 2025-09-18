_LOCATION_HOURS_REDSHIFT_QUERY = """
    SELECT
        {redshift_table}.location_id,
        {redshift_table}.regular_open,
        {redshift_table}.regular_close
    FROM {redshift_table}
    WHERE {redshift_table}.is_current
        AND {redshift_table}.weekday = '{weekday}';"""

_UPDATE_QUERY = """
    UPDATE {redshift_table}
    SET is_current = False
    WHERE weekday = '{weekday}'
        AND location_id IN ({stale_locations_str})
        AND date_of_change < '{today}';"""


def build_location_hours_redshift_query(redshift_table, weekday):
    return _LOCATION_HOURS_REDSHIFT_QUERY.format(
        redshift_table=redshift_table, weekday=weekday
    )


def build_update_query(redshift_table, weekday, stale_locations_str, today):
    return _UPDATE_QUERY.format(
        redshift_table=redshift_table,
        weekday=weekday,
        stale_locations_str=stale_locations_str,
        today=today,
    )
