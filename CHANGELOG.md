## 2025-12-04 -- v2.0.2
### Added
- Collect system-wide alerts

### Fixed
- Allow for NULL closing start/end dates (as long as one is filled)

## 2025-09-29 -- v2.0.1
### Fixed
- Allow for one location id with multiple names
- Ignore divisions/centers for now

## 2025-09-03 -- v2.0.0
### Added
- Use new Drupal API instead of deprecated Refinery API
- Update both the hours and alerts schemas to v2

## 2025-03-10 -- v1.0.5
### Fixed
- Do not log an error when QA Refinery is down

## 2024-03-19 -- v1.0.4
### Fixed
- If all libraries are closed on a day (Sundays), use a placeholder for the earliest
opening/latest closing instead of throwing an error

## 2023-11-17 -- v1.0.3
### Fixed
- Do not log a warning for new locations in QA

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