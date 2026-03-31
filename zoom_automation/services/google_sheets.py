import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# zoom_automation/ is now the root — config/ sits directly inside it
BASE_DIR = Path(__file__).resolve().parents[1]  # services/ -> zoom_automation/ -> project root
SERVICE_ACCOUNT_FILE = BASE_DIR / "config" / "service_account.json"


def get_spreadsheet(sheet_id):
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id)


def get_all_worksheets(spreadsheet):
    return spreadsheet.worksheets()


def validate_structure(sheet, required_columns):
    headers = sheet.row_values(1)
    missing = [col for col in required_columns if col not in headers]
    if missing:
        return False, missing
    return True, []


def get_column_index(sheet):
    headers = sheet.row_values(1)
    return {name: idx + 1 for idx, name in enumerate(headers)}


def update_row(sheet, row_number, col_index, meeting_id, password, join_url):
    sheet.update_cell(row_number, col_index["Status"], "Created")
    sheet.update_cell(row_number, col_index["MeetingID"], meeting_id)
    sheet.update_cell(row_number, col_index["Passcode"], password)
    sheet.update_cell(row_number, col_index["JoinURL"], join_url)