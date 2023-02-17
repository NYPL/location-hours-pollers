# LocationHoursPoller

The LocationHoursPoller has two modes:
* The `LOCATION_HOURS` mode periodically checks [Refinery](https://refinery.nypl.org/api/nypl/locations/v1.0/locations) for each library's regular hours, checks them against what's already stored in Redshift, and writes any newly updated hours to LocationHours Kinesis streams for ingest into the [BIC](https://github.com/NYPL/BIC)
* The `LOCATION_CLOSURE_ALERTS` mode periodically checks [Refinery](https://refinery.nypl.org/api/nypl/locations/v1.0/locations) for any library closure alerts and writes them to LocationClosureAlert Kinesis streams for ingest into the [BIC](https://github.com/NYPL/BIC).

## Running locally
* `cd` into this directory
* Add your AWS profile `AWS_PROFILE` to the config file for the environment you want to run
  * Alternatively, you can manually export it (e.g. `export AWS_PROFILE=nypl-digital-dev`)
* Run `ENVIRONMENT=<env> python3 main.py`
  * `<env>` should be the config filename without the `.yaml` suffix. The `location_hours_<>` files run the poller in `LOCATION_HOURS` mode and the the `location_closure_alerts_<>` files run the poller in `LOCATION_CLOSURE_ALERTS` mode.
  * `make run-hours` will run the poller in `LOCATION_HOURS` mode using the development environment
  * `make run-closure-alerts` will run the poller in `LOCATION_CLOSURE_ALERTS` mode using the development environment
* Alternatively, to build and run a Docker container, run:
```
docker image build -t location-hours-poller:local .

docker container run -e ENVIRONMENT=<env> -e AWS_PROFILE=<aws_profile> location-hours-poller:local
```

## Git workflow
This repo uses the [Main-QA-Production](https://github.com/NYPL/engineering-general/blob/main/standards/git-workflow.md#main-qa-production) git workflow.

[`main`](https://github.com/NYPL/location-hours/tree/main) has the latest and greatest commits, [`qa`](https://github.com/NYPL/location-hours/tree/qa) has what's in our QA environment, and [`production`](https://github.com/NYPL/location-hours/tree/production) has what's in our production environment.

### Ideal Workflow
- Cut a feature branch off of `main`
- Commit changes to your feature branch
- File a pull request against `main` and assign a reviewer
  - In order for the PR to be accepted, it must pass all unit tests, have no lint issues, and update the CHANGELOG (or contain the Skip-Changelog label in GitHub)
- After the PR is accepted, merge into `main`
- Merge `main` > `qa`
- Deploy app to QA and confirm it works
- Merge `qa` > `production`
- Deploy app to production and confirm it works

## Environment variables
Note that the QA and production env files are actually read by the deployed service, so do not change these files unless you want to change how the service will behave in the wild -- these are not meant for local testing.

| Name        | Notes           |
| ------------- | ------------- |
| `AWS_REGION` | Always `us-east-1`. The AWS region used for the Redshift, KMS, and Kinesis clients. |
| `LOCATIONS_API_URL` | Always `https://refinery.nypl.org/api/nypl/locations/v1.0/locations`. API endpoint to which the poller sends location requests. |
| `KINESIS_BATCH_SIZE` | How many records should be sent to Kinesis at once. Kinesis supports up to 500 records per batch. |
| `LOG_LEVEL` (optional) | What level of logs should be output. Set to `info` by default. |
| `MODE` | Mode to run the poller in. Either `LOCATION_HOURS` or `LOCATION_CLOSURE_ALERTS`. |
| `KINESIS_STREAM_ARN` | Encrypted ARN for the Kinesis stream the poller sends the encoded data to |
| `LOCATION_CLOSURE_ALERT_SCHEMA_URL` | Platform API endpoint from which to retrieve the LocationClosureAlert Avro schema |
| `LOCATION_HOURS_SCHEMA_URL` | Platform API endpoint from which to retrieve the LocationHours Avro schema |
| `REDSHIFT_DB_NAME` | Which Redshift database to query (either `dev`, `qa`, or `production`) |
| `REDSHIFT_TABLE` | Which Redshift table to query |
| `REDSHIFT_DB_HOST` | Encrypted Redshift cluster endpoint |
| `REDSHIFT_DB_USER` | Encrypted Redshift user |
| `REDSHIFT_DB_PASSWORD` | Encrypted Redshift password for the user |
