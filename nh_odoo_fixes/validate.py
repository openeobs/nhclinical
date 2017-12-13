# -*- coding: utf-8 -*-
"""
A place for generic validation functions.

In some places the variable name `date_time` has been used to avoid conflict
with the imported `datetime` class.
"""
from datetime import datetime

from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


def not_in_the_future_multiple_args(*args):
    for arg in args:
        if arg:
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


def in_min_max_range(min_value, max_value, value):
    """
    Validates that a value is within a range given by the passed minimum and
    maximum values. The value is allowed to be equal to the minimum and
    maximum but not less than or greater than.
    :param min_value:
    :param max_value:
    :param value:
    :raises: ValidationError
    """
    if value < min_value:
        raise ValidationError(
            "Value '{}' is less than the minimum valid value '{}'".format(
                value, min_value)
        )
    if value > max_value:
        raise ValidationError(
            "Value '{}' is greater than the maximum valid value '{}'".format(
                value, max_value)
        )


def fields_in_min_max_range(record, field_names_to_validate):
    """
    This method has a very specific use case. A model may be used for
    something like configuration and may have fields like `temperature`,
    `temperature_minimum`, and `temperature_maximum`. The method will take a
    record with all its fields populated and validate that each 'normal' field
    is within the range specified by its corresponding minimum and maximum
    fields.

    Any model that has fields that follow the naming convention demonstrated
    above can use this method for validation.
    :param record:
    :param field_names_to_validate:
    :type field_names_to_validate: dict
    :return:
    """
    for field_name in field_names_to_validate:
        minimum_field_name = record._fields[field_name].min
        maximum_field_name = record._fields[field_name].max

        minimum = getattr(record, minimum_field_name)
        maximum = getattr(record, maximum_field_name)

        field_value = getattr(record, field_name)
        in_min_max_range(minimum, maximum, field_value)


def validate_non_empty_string(string):
    """
    Validate that string is not empty.
    :param string: String to validate.
    :return: If string is empty or not.
    """
    if string is None or string is False:
        return False
    clean_string = unicode(string).strip()
    if len(clean_string) < 1:
        return False
    return True
