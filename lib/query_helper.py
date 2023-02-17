import os

_LOCATION_HOURS_REDSHIFT_QUERY = '''
    SELECT DISTINCT ON (location_code)
        location_code, open, close
    FROM public.{redshift_table}
    WHERE weekday = {weekday}
    ORDER BY location_code, date_of_change DESC;'''


def build_location_hours_redshift_query(weekday):
    return _LOCATION_HOURS_REDSHIFT_QUERY.format(
        redshift_table=os.environ['REDSHIFT_TABLE'],
        weekday=weekday)
