from datetime import datetime
import pytz


def convert_and_fill_all(row):

    pacific_col = row.get("Date & Time PDT/PST")
    utc_col = row.get("Date & Time UTC")
    ist_col = row.get("Date & Time IST")

    pacific = pytz.timezone("America/Los_Angeles")
    ist = pytz.timezone("Asia/Kolkata")
    utc = pytz.utc

    try:
        if ist_col:
            dt = parse_time(ist_col)
            source_time = ist.localize(dt)

        elif utc_col:
            dt = parse_time(utc_col)
            source_time = utc.localize(dt)

        elif pacific_col:
            dt = parse_time(pacific_col)
            source_time = pacific.localize(dt)

        else:
            return None, None, None, None

        pacific_time = source_time.astimezone(pacific)
        utc_time = source_time.astimezone(utc)
        ist_time = source_time.astimezone(ist)

        pacific_iso = pacific_time.strftime("%Y-%m-%dT%H:%M:%S")

        return (
            pacific_iso,  # For Zoom
            pacific_time.strftime("%a, %b %d @ %I:%M %p"),
            utc_time.strftime("%a, %b %d @ %I:%M %p"),
            ist_time.strftime("%a, %b %d @ %I:%M %p"),
        )

    except Exception as e:
        print("Time Conversion Error:", e)
        return None, None, None, None


def parse_time(time_str):
    cleaned = (
        time_str.replace("@", "")
        .replace(",", ", ")
        .strip()
        .title()
    )

    dt = datetime.strptime(cleaned, "%a, %b %d %I:%M %p")
    return dt.replace(year=datetime.now().year)