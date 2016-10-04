# -*- coding: utf-8 -*-
"""
A place for generic validation functions.

In some places the variable name `date_time` has been used to avoid conflict
with the imported `datetime` class.
"""
from datetime import datetime

from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

def not_in_the_future(*args):
    for arg in args:
        not_in_the_future(arg)


def not_in_the_future(date_time):
    date_time = _convert_string_to_datetime(date_time)

    now = datetime.now()
    if date_time > now:
        raise ValidationError("Date cannot be in the future.")

def start_datetime_not_after_end_datetime(start_datetime, end_datetime):
    start_datetime = _convert_string_to_datetime(start_datetime)
    end_datetime = _convert_string_to_datetime(end_datetime)

    if start_datetime > end_datetime:
        raise ValidationError("The start date cannot be after the end date.")

def _convert_string_to_datetime(date_time):
    if isinstance(date_time, basestring):
        date_time = datetime.strptime(date_time, DTF)
    elif isinstance(date_time, datetime):
        pass
    else:
        raise TypeError("This function only accepts str or datetime objects. "
                        "{invalid_type} is not a valid type."
                        .format(invalid_type=type(date_time)))
    return date_time