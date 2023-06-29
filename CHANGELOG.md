## 2023-06-28 -- v1.0.2
### Fixed
- Updated `configure-aws-credentials` GitHub action version
- Updated `nypl-py-utils` version
- Explicitly use ISO 8601 format for dates and times

## 2023-06-05 -- v1.0.1
### Fixed
- Fixed production ECS cluster/service names in deploy-production GitHub workflow

## 2023-06-02 -- v1.0.0
### Added
- Log a warning if the earliest library opening and/or the latest library closing changes

## 2023-04-12 -- v0.0.4
### Added
- Updated output records to use new LocationHours and LocationClosureAlert schema fields

## 2023-03-23 -- v0.0.3
### Added
- Added Github Actions workflows for deployment

## 2023-02-24 -- v0.0.2
### Fixed
- Updated Redshift query, as DISTINCT ON is not supported by Redshift SQL

## 2023-02-16 -- v0.0.1
### Added
- Initial commit