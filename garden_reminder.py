import os
import smtplib
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText

import pandas as pd
from aspose.cells import Workbook
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


def read_garden_data(file_path):
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


def parse_date(date_str):
    dt = parser.parse(date_str)
    date = dt.date()
    return date


def check_due_plants(df):
    today = datetime.today().date()
    due_water = []
    due_fertilizer = []

    for _, row in df.iterrows():
        common_name = row[COMMON_NAME_FIELD]
        scientific_name = row.get(SCIENTIFIC_NAME_FIELD, "")
        location = row.get(LOCATION_FIELD, "")
        plant_id = f"{common_name} [{scientific_name}] ({location})"
        # In case of missing scientific name or location, remove empty [] and ()
        plant_id = plant_id.replace("[]", "").replace("()", "")
        last_watered_date = parse_date(row[LAST_WATERED_FIELD]) if not pd.isna(row[LAST_WATERED_FIELD]) else pd.NA
        last_fertilized_date = parse_date(row[LAST_FERTILIZED_FIELD]) if not pd.isna(row[LAST_FERTILIZED_FIELD]) else pd.NA

        if pd.isna(last_watered_date) or (today - last_watered_date).days >= row[MAX_WATER_INTERVAL_FIELD]:
            due_water.append(plant_id)
        if pd.isna(last_fertilized_date) or (today - last_fertilized_date).days >= row[MAX_FERTILIZE_INTERVAL_FIELD]:
            due_fertilizer.append(plant_id)

    return due_water, due_fertilizer


def send_reminder_email(water_list, fertilizer_list):
    
    if not water_list and not fertilizer_list:
        return

    body = ""
    if water_list:
        body += "🌱 **Plants needing watering today**:\n•\t" + "\n•\t".join(water_list) + "\n\n"
    if fertilizer_list:
        body += "🌿 **Plants needing fertilizing today**:\n•\t" + "\n•\t".join(fertilizer_list)

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
