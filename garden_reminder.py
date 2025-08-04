import os
import re
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

import pandas as pd
from aspose.cells import Workbook
from dateutil import parser
from dotenv import load_dotenv

# Load in email configuration parameters and custom field names
load_dotenv()
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
REMINDER_SUBJECT = os.getenv("EMAIL_SUBJECT", "Daily Plant Care Reminder")

FILE_PATH = os.getenv("FILE_PATH")
LAST_WATERED_FIELD = os.getenv("LAST_WATERED_FIELD", "Last Watered")
LAST_FERTILIZED_FIELD = os.getenv("LAST_FERTILIZED_FIELD", "Last Fertilized")
MAX_WATER_INTERVAL_FIELD = os.getenv("MAX_WATER_INTERVAL_FIELD", "Max Watering Interval")
MAX_FERTILIZE_INTERVAL_FIELD = os.getenv("MAX_FERTILIZE_INTERVAL_FIELD", "Max Fertilizing Interval")
COMMON_NAME_FIELD = os.getenv("COMMON_NAME_FIELD", "Common name")
SCIENTIFIC_NAME_FIELD = os.getenv("SCIENTIFIC_NAME_FIELD", "Latin name")
LOCATION_FIELD = os.getenv("LOCATION_FIELD", "Location")


def read_garden_data(file_path: str) -> pd.DataFrame:
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path, parse_dates=[LAST_WATERED_FIELD, LAST_FERTILIZED_FIELD])
        # Drop aspose watermark (added if .csv file was converted from .numbers using aspose.cells.Workbook)
        # Located in final row, first column
        if "Aspose.Cells" in df.iloc[-1, 0]:
            df = df.iloc[:-1]
    elif file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path, parse_dates=[LAST_WATERED_FIELD, LAST_FERTILIZED_FIELD])
    elif file_path.endswith(".numbers"):
        # Convert .numbers file to .csv and then read that instead
        numbers_workbook = Workbook(file_path)
        csv_path = file_path.replace(".numbers", ".csv")
        numbers_workbook.save(csv_path)
        return read_garden_data(csv_path)
    else:
        raise ValueError(f"Could not parse file {file_path}")
    return df


def parse_date(date_str: str):
    if isinstance(date_str, pd.Timestamp):
        return date_str.date()
    dt = parser.parse(date_str)
    date = dt.date()
    return date


def check_due_plants(df: pd.DataFrame) -> tuple[dict, dict]:
    today = datetime.today().date()
    due_water = {}
    due_fertilizer = {}

    for _, row in df.iterrows():
        common_name = row[COMMON_NAME_FIELD]
        scientific_name = row.get(SCIENTIFIC_NAME_FIELD, "")
        location = row.get(LOCATION_FIELD, "")
        plant_id = f"{common_name} [{scientific_name}] ({location})"
        # In case of missing scientific name or location, remove empty [] and ()
        plant_id = re.sub(r"[\[\(](nan)?[\]\)]", "", plant_id)
        last_watered_date = parse_date(row[LAST_WATERED_FIELD]) if not pd.isna(row[LAST_WATERED_FIELD]) else pd.NA
        last_fertilized_date = parse_date(row[LAST_FERTILIZED_FIELD]) if not pd.isna(row[LAST_FERTILIZED_FIELD]) else pd.NA

        if pd.isna(last_watered_date):
            due_water[plant_id] = "last watering date unknown"
        elif (today - last_watered_date).days >= row[MAX_WATER_INTERVAL_FIELD]:
            days_ago = (today - last_watered_date).days
            last_watered_date = last_watered_date.strftime("%Y-%m-%d")
            due_water[plant_id] = f"last watered {days_ago} days ago ({last_watered_date})"
        if pd.isna(last_fertilized_date):
            due_fertilizer[plant_id] = "last fertilization date unknown"
        elif (today - last_fertilized_date).days >= row[MAX_FERTILIZE_INTERVAL_FIELD]:
            days_ago = (today - last_fertilized_date).days
            last_fertilized_date = last_fertilized_date.strftime("%Y-%m-%d")
            due_fertilizer[plant_id] = f"last fertilized {days_ago} days ago ({last_fertilized_date})"


    # Check whether plants due for watering are also due for fertilizing
    ids_to_delete = set()
    for plant_id in due_water:
        if plant_id in due_fertilizer:
            due_fertilizer[plant_id] = f"{due_water[plant_id]} and {due_fertilizer[plant_id]}"
            ids_to_delete.add(plant_id)
    for plant_id in ids_to_delete:
        del due_water[plant_id]

    return due_water, due_fertilizer


def send_reminder_email(plants_to_be_watered: dict = None,
                        plants_to_be_fertilized: dict = None
                        ):
    if not plants_to_be_watered and not plants_to_be_fertilized:
        return

    body = ""
    if plants_to_be_fertilized:
        body += "🌿 **Plants needing watering AND fertilizing today**:"
        for plant_id, latest_date in plants_to_be_fertilized.items():
            body += f"\n\n•\t{plant_id}\n\t{latest_date}"
    if plants_to_be_watered and plants_to_be_fertilized:
        body += "\n\n\n"
    if plants_to_be_watered:
        body += "🌱 **Plants needing watering today**:"
        for plant_id, latest_date in plants_to_be_watered.items():
            body += f"\n\n•\t{plant_id}\n\t{latest_date}"

    msg = MIMEText(body)
    msg["Subject"] = REMINDER_SUBJECT
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())


def main():
    df = read_garden_data(os.path.abspath(FILE_PATH))
    water_due, fert_due = check_due_plants(df)
    send_reminder_email(water_due, fert_due)


if __name__ == "__main__":
    main()
