import datetime
import frappe

class EthiopianDateConverter:
    JD_OFFSET = 1723856

    @staticmethod
    def is_ethiopian_leap_year(year):
        # Ethiopian leap year: remainder when divided by 4 equals 3.
        return (year % 4) == 3

    @staticmethod
    def ethiopian_to_gregorian(ethiopian_year, ethiopian_month, ethiopian_day):
        """
        Convert an Ethiopian date to Gregorian.
        """
        ETHIOPIAN_EPOCH = 2796
        # Ethiopian months: first 11 months have 30 days; the 12th has 35 days.
        ETHIOPIAN_MONTH_DAYS = [30] * 11 + [35]

        julian_day = ETHIOPIAN_EPOCH
        # Add days for complete years passed.
        for i in range(1, ethiopian_year):
            julian_day += 365
            if EthiopianDateConverter.is_ethiopian_leap_year(i):
                julian_day += 1

        # Add days for complete months passed in the current year.
        for i in range(1, ethiopian_month):
            julian_day += ETHIOPIAN_MONTH_DAYS[i - 1]

        # Add the days for the current month (subtract one to adjust).
        julian_day += ethiopian_day - 1

        # Adjustment for the 13th month.
        if ethiopian_month == 13:
            julian_day -= 5

        gregorian_date = datetime.date.fromordinal(julian_day)
        return gregorian_date.strftime("%Y-%m-%d")

    @staticmethod
    def gregorian_to_ethiopian(year, month, day):
        """
        Convert Gregorian date (year, month, day) to Ethiopian date string in DD/MM/YYYY format.
        """
        jdn = EthiopianDateConverter.to_jdn(year, month, day)
        ethiopian_date = EthiopianDateConverter.to_ethiopian_date(jdn)
        return EthiopianDateConverter.format_ethiopian_date(ethiopian_date)

    @staticmethod
    def to_jdn(year, month, day):
        a = (14 - month) // 12
        y = year + 4800 - a
        m = month + 12 * a - 3
        return day + ((153 * m + 2) // 5) + 365 * y + (y // 4) - (y // 100) + (y // 400) - 32045

    @staticmethod
    def to_ethiopian_date(jdn):
        r = (jdn - EthiopianDateConverter.JD_OFFSET) % 1461
        n = (r % 365) + 365 * (r // 1460)
        year = 4 * ((jdn - EthiopianDateConverter.JD_OFFSET) // 1461) + (r // 365) - (r // 1460)
        month = (n // 30) + 1
        day = (n % 30) + 1
        return {"year": year, "month": month, "day": day}

    @staticmethod
    def format_ethiopian_date(date_dict):
        # Format as "DD/MM/YYYY"
        return "{:02d}/{:02d}/{:04d}".format(date_dict["day"], date_dict["month"], date_dict["year"])

@frappe.whitelist()
def ethiopian_to_gregorian(ethiopian_date):
    """
    Convert an Ethiopian date string (format "DD/MM/YYYY") to a Gregorian date string ("YYYY-MM-DD").
    Validates that the Ethiopian date string is exactly 10 characters.
    """
    if  len(ethiopian_date) == 10:
       
        try:
            day, month, year = map(int, ethiopian_date.split('/'))
        except Exception as e:
            frappe.throw("Error parsing Ethiopian date. Ensure the format is 'DD/MM/YYYY'. " + str(e))
        return EthiopianDateConverter.ethiopian_to_gregorian(year, month, day)
    # else:
    #   frappe.throw("!Invalid Ethiopian date format. It must be in 'DD/MM/YYYY' format.")

@frappe.whitelist()
def gregorian_to_ethiopian(gregorian_date):
    """
    Convert a Gregorian date string (format "YYYY-MM-DD") to an Ethiopian date string ("DD/MM/YYYY").
    """
    try:
        year, month, day = map(int, gregorian_date.split('-'))
    except Exception as e:
        frappe.throw("Error parsing Gregorian date. Ensure the format is 'YYYY-MM-DD'. " + str(e))
    return EthiopianDateConverter.gregorian_to_ethiopian(year, month, day)
