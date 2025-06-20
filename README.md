# HomeReminders


## Table of Contents
* [Introduction](#introduction)
* [Setup](#setup)
* [Tools](#tools)
    * [Garden Watering + Fertilizing](#garden-watering--fertilizing-reminders)
* [cronjobs](#cronjobs)

# Introduction
This repository contains tools for automating reminders for home and garden upkeep.
Currently available reminders:
- Garden watering + fertilizing


# Setup
To set up the Python environment for the first time, run:
```
./setup.sh
```
Subsequently, one needs only to activate the virtual environment (venv) or configure it as default for the project in one's IDE of choice.

# Tools
## Garden Watering + Fertilizing Reminders
This tool parses a data file (.xlsx, .csv, or .numbers) containing information about plants in one's garden or home and sends an email summary listing which of those plants are due for watering and/or fertilizing, given when they were last watered/fertilized and specifications on how often this should be performed per plant.
An example CSV data file with one plant is included at `garden.csv`.

This tool requires an `.env` file, minimally including one's email configuration settings and full path to the data file. Please use the following template and fill in your own email address, server, port, email app password, and path to garden data file. 

```
EMAIL_SENDER=your_email@example.com
EMAIL_RECEIVER=receiver@example.com
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_email@example.com
SMTP_PASSWORD=your_app_password
FILE_PATH="/path/to/your/garden/data.csv"
```
(!) NOTE: It is more secure to set and use an app password than your actual email account password! See, e.g. [here](https://myaccount.google.com/apppasswords) for Gmail accounts. 

Optionally, you can customize your input file column names and email subject line, and can specify these in the `.env` file as well. The values below are the defaults:
``` 
EMAIL_SUBJECT="Daily Plant Care Reminder"
LAST_WATERED_FIELD="Last Watered"
LAST_FERTILIZED_FIELD="Last Fertilized"
MAX_WATER_INTERVAL_FIELD="Max Watering Interval"
MAX_FERTILIZE_INTERVAL_FIELD="Max Fertilizing Interval"
COMMON_NAME_FIELD="Common name"
SCIENTIFIC_NAME_FIELD="Latin name"
LOCATION_FIELD="Location"
```

Note that `MAX_WATER_INTERVAL_FIELD` and `MAX_FERTILIZE_INTERVAL_FIELD` refer to the column which specifies the maximum interval (in days) between waterings/fertilizing per plant.

The `LOCATION_FIELD` and `SCIENTIFIC_NAME_FIELD` are not required.

This script can then be run, either manually:
```
python garden_reminder.py
```
or it can be configured as a [cronjob](#cronjobs) to run automatically on certain days and/or at certain times.


# cronjobs
To set up a cronjob for a tool, access the crontab by running `crontab -e`.

Then add one or more cronjob entries, e.g. to run the `garden_reminder.py` tool every day at 8:30 AM:
```
30 08 * * * /path/to/your/venv/bin/python /path/to/your/garden_reminder.py
```
