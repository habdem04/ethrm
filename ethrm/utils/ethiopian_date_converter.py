# utils/ethiopian_date_converter.py

import datetime

class EthiopianDateConverter:
    JD_OFFSET = 1723856  # Used for JDN conversion calculations

    @staticmethod
    def is_ethiopian_leap_year(year):
        return (year % 4) == 3

    @staticmethod
    def ethiopian_to_gregorian(ethiopian_date_str):
        """
        Convert an Ethiopian date string in "DD/MM/yyyy" format (10 characters) 
        to a Gregorian date string in "DD-MM-yyyy" format.
        """
        # Check input length
        if not ethiopian_date_str or len(ethiopian_date_str) != 10:
            raise ValueError("Invalid Ethiopian date format. Expected format is DD/MM/yyyy (10 characters)")
        
        try:
            day, month, year = map(int, ethiopian_date_str.split('/'))
        except ValueError:
            raise ValueError("Invalid Ethiopian date format. Expected format is DD/MM/yyyy")
        
        ETHIOPIAN_EPOCH = 2796
        ETHIOPIAN_MONTH_DAYS = [30] * 12 + [35]

        # Start calculation from the Ethiopian epoch
        julian_day = ETHIOPIAN_EPOCH

        # Add days for complete years
        for i in range(1, year):
            julian_day += 365
            if EthiopianDateConverter.is_ethiopian_leap_year(i):
                julian_day += 1

        # Add days for complete months in the given year
        for i in range(1, month):
            julian_day += ETHIOPIAN_MONTH_DAYS[i - 1]

        # Add days in the current month (adjusting by subtracting 1)
        julian_day += day - 1

        # Adjustment for the 13th month (Pagumen)
        if month == 13:
            julian_day -= 5

        # Convert the custom-calculated Julian day into a Gregorian date
        gregorian_date = EthiopianDateConverter.julian_day_to_date(julian_day)
        return EthiopianDateConverter.format_date(gregorian_date)

    @staticmethod
    def gregorian_to_ethiopian(gregorian_date_str):
        """
        Convert a Gregorian date string in "DD-MM-yyyy" format (10 characters) 
        to an Ethiopian date string in "DD/MM/yyyy" format.
        """
        if not gregorian_date_str or len(gregorian_date_str) != 10:
            raise ValueError("Invalid Gregorian date format. Expected format is DD-MM-yyyy (10 characters)")
            
        try:
            day, month, year = map(int, gregorian_date_str.split('-'))
        except ValueError:
            raise ValueError("Invalid Gregorian date format. Expected format is DD-MM-yyyy")
            
        jdn = EthiopianDateConverter.to_jdn(year, month, day)
        ethiopian_date = EthiopianDateConverter.to_ethiopian_date(jdn)
        return EthiopianDateConverter.format_ethiopian_date(ethiopian_date)

    @staticmethod
    def to_jdn(year, month, day):
        a = (14 - month) // 12
        y = year + 4800 - a
        m = month + 12 * a - 3
        jdn = day + ((153 * m + 2) // 5) + 365 * y
        jdn += (y // 4) - (y // 100) + (y // 400) - 32045
        return jdn

    @staticmethod
    def to_ethiopian_date(jdn):
        r = (jdn - EthiopianDateConverter.JD_OFFSET) % 1461
        n = (r % 365) + 365 * (r // 1460)
        year = 4 * ((jdn - EthiopianDateConverter.JD_OFFSET) // 1461) + (r // 365) - (r // 1460)
        month = (n // 30) + 1
        day = (n % 30) + 1
        return {'day': day, 'month': month, 'year': year}

    @staticmethod
    def julian_day_to_date(julian_day):
        """
        Mimic the JavaScript logic:
          - Subtract the Unix epoch (719163)
          - Multiply by the number of milliseconds per day, then use utcfromtimestamp.
        """
        millis_per_day = 86400000
        unix_epoch = 719163
        unix_time = (julian_day - unix_epoch) * millis_per_day  # milliseconds
        # Convert milliseconds to seconds for utcfromtimestamp
        return datetime.datetime.utcfromtimestamp(unix_time / 1000.0)

    @staticmethod
    def format_date(date):
        # Return Gregorian date in "DD-MM-yyyy" format
        return date.strftime('%d-%m-%Y')

    @staticmethod
    def format_ethiopian_date(date):
        # Return Ethiopian date in "DD/MM/yyyy" format
        return f"{date['day']:02d}/{date['month']:02d}/{date['year']:04d}"
