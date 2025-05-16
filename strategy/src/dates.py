""" Helpers for date and time calculations. """

from datetime import date, datetime, timedelta, timezone


def is_last_day_of_month(check_date: date = date.today()) -> bool:
    """Returns True if the given date is the last day of its month."""
    next_day = check_date + timedelta(days=1)
    return next_day.day == 1


def is_first_day_of_month(check_date: date = date.today()) -> bool:
    """Returns True if the given date is the first day of its month."""
    return check_date.day == 1


def get_previous_month_start() -> int:
    """
    Calculates the start datetime in ms of the previous calendar month.

    Returns:
        int: Start of the previous month in ms.
    """
    now = datetime.now(timezone.utc)
    first_day_this_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    last_day_prev_month = first_day_this_month - timedelta(days=1)

    start_prev_month = datetime(
        last_day_prev_month.year, last_day_prev_month.month, 1, tzinfo=timezone.utc
    )

    return int(start_prev_month.timestamp() * 1000)
