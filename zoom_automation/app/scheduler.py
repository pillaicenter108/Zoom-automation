"""
scheduler.py
────────────
Standalone script that reads a Google Sheet and bulk-creates Zoom meetings
for all rows with Status = "pending".

Run independently of the UI:
    python scheduler.py --sheet <GOOGLE_SHEET_ID>
    python scheduler.py --sheet <GOOGLE_SHEET_ID> --dry-run
"""

import argparse
import sys
from dotenv import load_dotenv

from zoom_automation.services.google_sheets import (
    get_spreadsheet,
    get_all_worksheets,
    validate_structure,
    get_column_index,
    update_row,
)
from zoom_automation.services.zoom_service import (
    ZOOM_ACCOUNTS,
    get_access_token,
    validate_user,
    create_meeting,
)
from zoom_automation.core.time_converter import convert_and_fill_all

load_dotenv()

REQUIRED_COLUMNS = [
    "Call Title", "Duration", "Zoom Account", "Status",
    "MeetingID", "Passcode", "JoinURL",
    "Date & Time PDT/PST", "Date & Time UTC", "Date & Time IST",
    "Recurrence", "Occurrences",
]


# ─────────────────────────────────────────
#  LOGGING HELPERS
#  ui=True  → use st.info / st.success / st.error (Streamlit)
#  ui=False → plain print (CLI)
# ─────────────────────────────────────────

def _logger(ui: bool):
    if ui:
        import streamlit as st
        return st.info, st.success, st.warning, st.error
    else:
        def info(m):    print(f"  🔎  {m}")
        def ok(m):      print(f"  ✅  {m}")
        def warn(m):    print(f"  ⚠️   {m}")
        def error(m):   print(f"  ❌  {m}", file=sys.stderr)
        return info, ok, warn, error


# ─────────────────────────────────────────
#  CORE LOGIC
# ─────────────────────────────────────────

def schedule_meetings(sheet_id: str, dry_run: bool = False, ui: bool = True) -> int:
    """
    Process all sheets in the given Google Spreadsheet.
    ui=True  → outputs via Streamlit (st.info / st.success / st.error)
    ui=False → outputs via print (CLI mode)
    Returns total number of meetings created.
    """
    log_info, log_ok, log_warn, log_error = _logger(ui)

    try:
        spreadsheet = get_spreadsheet(sheet_id)
        worksheets  = get_all_worksheets(spreadsheet)
    except Exception as e:
        log_error(f"Could not open spreadsheet: {e}")
        return 0

    total_created = 0

    for sheet in worksheets:
        log_info(f"Processing sheet: **{sheet.title}**")

        valid, missing = validate_structure(sheet, REQUIRED_COLUMNS)
        if not valid:
            log_error(f"Sheet '{sheet.title}' is missing columns: {missing}")
            continue

        col_index = get_column_index(sheet)
        records   = sheet.get_all_records()
        pending   = [(i + 2, row) for i, row in enumerate(records)
                     if str(row.get("Status", "")).strip().lower() == "pending"]

        log_info(f"Found **{len(pending)}** pending row(s) in {sheet.title}")

        for row_num, row in pending:
            # normalize to match ZOOM_ACCOUNTS keys e.g. "zoom 1", "zoom 2"
            import re as _re
            raw_account = str(row.get("Zoom Account", "")).strip().lower()
            zoom_account = _re.sub(r'(zoom)(\d)', lambda m: m.group(1) + ' ' + m.group(2), raw_account)

            if zoom_account not in ZOOM_ACCOUNTS:
                log_error(f"Row {row_num}: unknown Zoom account '{zoom_account}'")
                continue

            # Validate Zoom credentials
            try:
                token      = get_access_token(zoom_account)
                host_email = ZOOM_ACCOUNTS[zoom_account]["host_email"]
                if not validate_user(host_email, token):
                    log_error(f"Row {row_num}: invalid host email '{host_email}'")
                    continue
            except Exception as e:
                log_error(f"Row {row_num}: auth error — {e}")
                continue

            # Parse times
            pacific_iso, pacific_display, utc_display, ist_display = convert_and_fill_all(row)
            if not pacific_iso:
                log_warn(f"Row {row_num}: no valid time found, skipping.")
                continue

            # Recurrence
            recurrence_value = str(row.get("Recurrence", "")).strip().lower()
            if recurrence_value == "yes":
                recurrence_type, repeat_interval, occurrences = "weekly", 1, row.get("Occurrences")
            else:
                recurrence_type = repeat_interval = occurrences = None

            title = row.get("Call Title", f"Row {row_num}")

            if dry_run:
                log_ok(f"[DRY RUN] Would create: **{title}** at {pacific_display} ({zoom_account})")
                continue

            # Create meeting
            try:
                meeting = create_meeting(
                    title, pacific_iso, row.get("Duration"),
                    zoom_account, recurrence_type, repeat_interval, occurrences
                )
            except Exception as e:
                log_error(f"Row {row_num}: Zoom API error — {e}")
                continue

            if meeting is None:
                log_error(f"Row {row_num}: meeting creation returned None.")
                continue

            # Write results back to sheet
            sheet.update_cell(row_num, col_index["Date & Time PDT/PST"], pacific_display)
            sheet.update_cell(row_num, col_index["Date & Time UTC"],     utc_display)
            sheet.update_cell(row_num, col_index["Date & Time IST"],     ist_display)
            update_row(
                sheet, row_num, col_index,
                meeting.get("id"),
                meeting.get("generated_passcode"),
                meeting.get("join_url"),
            )

            total_created += 1
            log_ok(f"Created: '{title}'  (ID: {meeting.get('id')})")

    return total_created


# ─────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Bulk-schedule Zoom meetings from a Google Sheet."
    )
    parser.add_argument(
        "--sheet", required=True,
        help="Google Sheet ID (the long string in the sheet URL)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would be created without actually calling the Zoom API"
    )
    args = parser.parse_args()

    print(f"\n{'═'*50}")
    print(f"  ZoomFlow Scheduler")
    print(f"  Sheet : {args.sheet}")
    print(f"  Mode  : {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"{'═'*50}")

    total = schedule_meetings(args.sheet, dry_run=args.dry_run, ui=False)

    print(f"\n{'═'*50}")
    print(f"  Done! {total} meeting(s) {'would be ' if args.dry_run else ''}created.")
    print(f"{'═'*50}\n")


if __name__ == "__main__":
    main()