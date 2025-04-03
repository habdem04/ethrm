import frappe
from datetime import datetime, timedelta

@frappe.whitelist()
def calculate_probation_end_date(start_date, in_probation_days):
    """
    Calculate the probation end date given the Date of Joining (start_date) and 
    the number of probation days (in_probation_days), skipping Sundays and holidays.
    
    :param start_date: A string in "YYYY-MM-DD" format.
    :param in_probation_days: A string or integer representing working days.
    :return: The probation end date as a string in "YYYY-MM-DD" format.
    """
    try:
        # Parse the start_date
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        frappe.logger().info(f"Parsed Start Date: {start_date}")

        # Get holidays from Holiday Lists
        holidays = get_holidays()
        frappe.logger().info(f"Holidays: {holidays}")

        working_days = 0
        current_date = start_date

        # Loop until we reach the required number of working days
        while working_days < int(in_probation_days):
            current_date += timedelta(days=1)
            # Exclude Sundays (weekday 6) and holidays
            if current_date.weekday() != 6 and current_date not in holidays:
                working_days += 1
            else:
                frappe.logger().info(f"Skipping Date: {current_date} (Sunday or Holiday)")

        return current_date.strftime("%Y-%m-%d")

    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="Error in calculate_probation_end_date")
        frappe.throw(f"Error calculating probation end date: {e}")

def get_holidays():
    """
    Fetch holiday dates from all active Holiday Lists.
    """
    holiday_lists = frappe.get_all("Holiday List", fields=["name"])
    holidays = []
    for holiday_list in holiday_lists:
        holiday_dates = frappe.get_all("Holiday", filters={"parent": holiday_list["name"]}, fields=["holiday_date"])
        holidays.extend([frappe.utils.getdate(date["holiday_date"]) for date in holiday_dates])
    return holidays
