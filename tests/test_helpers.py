import os


class TestHelpers:
    ENV_VARS = {
        'ENVIRONMENT': 'test_environment',
        'AWS_REGION': 'test_aws_region',
        'LOCATIONS_API_URL': 'https://test_locations_api',
        'KINESIS_BATCH_SIZE': '2',
        'KINESIS_STREAM_ARN': 'test_kinesis_stream',
        'LOCATION_CLOSURE_ALERT_SCHEMA_URL':
            'https://test_closure_alert_schema',
        'LOCATION_HOURS_SCHEMA_URL': 'https://test_hours_schema',
        'REDSHIFT_DB_NAME': 'test_redshift_name',
        'REDSHIFT_TABLE': 'test_redshift_table',
        'REDSHIFT_DB_HOST': 'test_redshift_host',
        'REDSHIFT_DB_USER': 'test_redshift_user',
        'REDSHIFT_DB_PASSWORD': 'test_redshift_password'
    }

    @classmethod
    def set_env_vars(cls):
        for key, value in cls.ENV_VARS.items():
            os.environ[key] = value

    @classmethod
    def clear_env_vars(cls):
        for key in cls.ENV_VARS.keys():
            if key in os.environ:
                del os.environ[key]
