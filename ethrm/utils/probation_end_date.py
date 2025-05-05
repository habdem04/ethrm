# ethrm/utils/probation_end_date.py

import frappe
from datetime import datetime, timedelta

@frappe.whitelist()
def calculate_probation_end_date(start_date):
    """
    Calculate the probation end date given the Date of Joining (start_date),
    using the number of probation days configured in the single DocType 'Probation Setting',
    skipping Sundays and holidays.

    :param start_date: A string in "YYYY-MM-DD" format.
    :return: The probation end date as a string in "YYYY-MM-DD" format.
    """
    try:
        # Parse the start date
        doj = datetime.strptime(start_date, "%Y-%m-%d").date()
        frappe.logger().info(f"Parsed Start Date: {doj}")

        # Fetch probation length from the single DocType
        settings = frappe.get_single("Probation Setting")
        probation_days = int(settings.probation_in_days or 0)
        frappe.logger().info(f"Probation Days from Setting: {probation_days}")

        # Get the list of holiday dates
        holidays = _get_holidays()
        frappe.logger().info(f"Holidays: {holidays}")

        working_days = 0
        current_date = doj

        # Count forward until we've accumulated probation_days working days
        while working_days < probation_days:
            current_date += timedelta(days=1)
            if current_date.weekday() != 6 and current_date not in holidays:
                working_days += 1
            else:
                frappe.logger().info(f"Skipping Date: {current_date} (Sunday or Holiday)")

        return current_date.strftime("%Y-%m-%d")

    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="Error in calculate_probation_end_date")
        frappe.throw(f"Error calculating probation end date: {e}")


def _get_holidays():
    """
    Fetch holiday dates from all active Holiday Lists.
    """
    holiday_lists = frappe.get_all("Holiday List", fields=["name"])
    holidays = []

    for hl in holiday_lists:
        dates = frappe.get_all(
            "Holiday",
            filters={"parent": hl["name"]},
            fields=["holiday_date"]
        )
        holidays.extend([frappe.utils.getdate(d["holiday_date"]) for d in dates])

    return holidays
