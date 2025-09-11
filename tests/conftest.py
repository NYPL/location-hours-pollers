import os
import pytest

from freezegun import freeze_time

# Sets OS vars for entire set of tests
TEST_ENV_VARS = {
    "ENVIRONMENT": "test_environment",
    "AWS_REGION": "test_aws_region",
    "KINESIS_BATCH_SIZE": "2",
    "BASE_SCHEMA_URL": "https://test_schema_url",
    "REDSHIFT_DB_NAME": "test_redshift_name",
    "REDSHIFT_TABLE": "test_redshift_table",
    "HOURS_KINESIS_STREAM_ARN": "test_hours_kinesis_stream",
    "CLOSURE_ALERT_KINESIS_STREAM_ARN": "test_closure_alert_kinesis_stream",
    "REDSHIFT_DB_HOST": "test_redshift_host",
    "REDSHIFT_DB_USER": "test_redshift_user",
    "REDSHIFT_DB_PASSWORD": "test_redshift_password",
}


@pytest.fixture(scope="session", autouse=True)
def tests_setup_and_teardown():
    # Will be executed before the first test
    os.environ.update(TEST_ENV_VARS)
    freezer = freeze_time("2023-01-01 01:23:45-05:00")
    freezer.start()

    yield

    # Will execute after the final test
    freezer.stop()
    for os_config in TEST_ENV_VARS.keys():
        if os_config in os.environ:
            del os.environ[os_config]
