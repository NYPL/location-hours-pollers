# LocationHoursPoller

The LocationHoursPoller has two modes:
* The `LOCATION_HOURS` mode periodically checks [Refinery](https://refinery.nypl.org/api/nypl/locations/v1.0/locations) for each library's regular hours, checks them against what's already stored in Redshift, and writes any newly updated hours to LocationHours Kinesis streams for ingest into the [BIC](https://github.com/NYPL/BIC)
* The `LOCATION_CLOSURE_ALERT` mode periodically checks [Refinery](https://refinery.nypl.org/api/nypl/locations/v1.0/locations) for any library closure alerts and writes them to LocationClosureAlert Kinesis streams for ingest into the [BIC](https://github.com/NYPL/BIC).

## Running locally
* `cd` into this directory
* Add your `AWS_PROFILE` to the config file for the environment you want to run
  * Alternatively, you can manually export it (e.g. `export AWS_PROFILE=nypl-digital-dev`)
* Run `ENVIRONMENT=<env> MODE=<mode> python3 main.py`
  * `<env>` should be the config filename without the `.yaml` suffix
  * `<mode>` should be either `LOCATION_HOURS` or `LOCATION_CLOSURE_ALERT`
  * `make run-hours` will run the poller in `LOCATION_HOURS` mode using the development environment
  * `make run-closure-alert` will run the poller in `LOCATION_CLOSURE_ALERT` mode using the development environment
* Alternatively, to build and run a Docker container, run:
```
docker image build -t location-hours-poller:local .

docker container run -e ENVIRONMENT=<env> -e MODE=<mode> -e AWS_PROFILE=<aws_profile> location-hours-poller:local
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

## Deployment
The poller is uploaded to a single ECR repository [here](https://us-east-1.console.aws.amazon.com/ecr/repositories/private/946183545209/location-hours-pollers) that's used by four ECS instances (qa and prod for both the location-hours-poller and the location-closure-alert-poller). To upload a new QA version of this service, create a new release in GitHub off of the `qa` branch and tag it either `qa-vX.X.X`, `qa-hours-vX.X.X`, or `qa-closure-alert-vX.X.X`. The GitHub Actions deploy-qa workflow will then upload the code to ECR and update the appropriate ECS service. To deploy to production, create the release from the `production` branch and tag it `production-vX.X.X`, `production-hours-vX.X.X`, or `production-closure-alert-vX.X.X`. Tagging the release `qa-vX.X.X` or `production-vX.X.X` will trigger both the hours and the closure alert ECS services to be updated; otherwise, only the tagged poller will be updated. To trigger the apps to run immediately (rather than waiting for the next scheduled event), run:
```bash
aws ecs run-task --cluster location-hours-poller-qa --task-definition location-hours-poller-qa:4 --count 1 --region us-east-1 --profile nypl-digital-dev

aws ecs run-task --cluster location-closure-alert-poller-qa --task-definition location-closure-alert-poller-qa:4 --count 1 --region us-east-1 --profile nypl-digital-dev
```

## Environment variables
Note that the QA and production env files are actually read by the deployed service, so do not change these files unless you want to change how the service will behave in the wild -- these are not meant for local testing.

| Name        | Notes           |
| ------------- | ------------- |
| `AWS_REGION` | Always `us-east-1`. The AWS region used for the Redshift, KMS, and Kinesis clients. |
| `LOCATIONS_API_URL` | API endpoint to which the poller sends location requests |
| `KINESIS_BATCH_SIZE` | How many records should be sent to Kinesis at once. Kinesis supports up to 500 records per batch. |
| `BASE_SCHEMA_URL` | Base URL for the Platform API endpoint from which to retrieve the Avro schemas |
| `REDSHIFT_DB_NAME` | Which Redshift database to query (either `qa` or `production`). Only used in `LOCATION_HOURS` mode. |
| `LOG_LEVEL` (optional) | What level of logs should be output. Set to `info` by default. |
| `HOURS_KINESIS_STREAM_ARN` | Encrypted ARN for the Kinesis stream the poller sends the encoded hours data to in `LOCATION_HOURS` mode |
| `CLOSURE_ALERT_KINESIS_STREAM_ARN` | Encrypted ARN for the Kinesis stream the poller sends the encoded alert data to in `LOCATION_CLOSURE_ALERT` mode |
| `REDSHIFT_DB_HOST` | Encrypted Redshift cluster endpoint. Only used in `LOCATION_HOURS` mode. |
| `REDSHIFT_DB_USER` | Encrypted Redshift user. Only used in `LOCATION_HOURS` mode. |
| `REDSHIFT_DB_PASSWORD` | Encrypted Redshift password for the user. Only used in `LOCATION_HOURS` mode. |
