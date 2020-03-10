[![CircleCI](https://circleci.com/gh/flywheel-apps/GRP-2.svg?style=svg)](https://circleci.com/gh/flywheel-apps/GRP-2)

# Metadata Error Reporter
An sdk gear that checks errors for resolution status and rolls it up into a report

It can be run on projects, subjects, or sessions.

#### Configuration
The config options are:
  - container_type: defaults to all (subject, session, and acquisition) or one specific container type
  - file_type: The file type of the report, defaults to json, can be switched to csv
  - filename: An optional override to the report name, defaults to `error-report-{container_type}-{timestamp}.{file_type}`

#### Summary
The gear finds the containers base on the `error` tag, but will re-validate the containers status using the contents of the error.log file.
For the gear to work, a validation gear must set an `error` tag and upload an `error.log` file that follows certain specifications.

#### Error Log
The error log file should be a json file ending in `error.log.json`. The format of it should be
```
[
	{
		"schema": {
			"type": "string"
		},
		"item": "session.info.my_field"
	}
	.
	.
	.
]
```

