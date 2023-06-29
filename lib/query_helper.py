_LOCATION_HOURS_REDSHIFT_QUERY = '''
    SELECT
        {redshift_table}.drupal_location_id,
        {redshift_table}.regular_open,
        {redshift_table}.regular_close
    FROM {redshift_table} INNER JOIN (
        SELECT drupal_location_id, weekday, MAX(date_of_change) AS last_date
        FROM {redshift_table}
        GROUP BY drupal_location_id, weekday
    ) x
    ON {redshift_table}.drupal_location_id = x.drupal_location_id
    AND {redshift_table}.weekday = x.weekday
    AND (
        {redshift_table}.date_of_change = x.last_date OR
        (x.last_date IS NULL AND {redshift_table}.date_of_change IS NULL)
    )
    WHERE {redshift_table}.weekday = '{weekday}';'''


def build_location_hours_redshift_query(redshift_table, weekday):
    return _LOCATION_HOURS_REDSHIFT_QUERY.format(
        redshift_table=redshift_table, weekday=weekday)
