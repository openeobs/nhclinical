# -*- coding: utf-8 -*-
"""Contains various useful methods for managing datetimes."""
from datetime import datetime

from openerp import models, api
from openerp.fields import Datetime
from openerp.osv import fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class DatetimeUtils(models.AbstractModel):
    """
    Various helpful methods for handling datetime.
    """
    _name = 'datetime_utils'

    time_format_front_end = '%H:%M'
    date_format_front_end = '%d/%m/%Y'
    date_format_front_end_two_character_year = \
        date_format_front_end.replace('%Y', '%y')
    format_string = '{} {}'

    datetime_format_front_end = format_string.format(time_format_front_end,
                                                     date_format_front_end)
    datetime_format_front_end_two_character_year = format_string.format(
        time_format_front_end, date_format_front_end_two_character_year
    )

    known_formats = [
        DTF,
        datetime_format_front_end,
        datetime_format_front_end_two_character_year
    ]

    @classmethod
    def zero_microseconds(cls, date_time):
        """
        Return the passed date_time with any microseconds set to 0.

        :param date_time:
        :type date_time: datetime or str
        :return:
        """
        if not (isinstance(date_time, datetime) or isinstance(date_time, str)):
            raise TypeError("Datetime or str required but {} was passed."
                            .format(type(date_time)))

        datetime_format = DTF + '.%f'
        if isinstance(date_time, str):
            date_time = datetime.strptime(date_time, datetime_format)
        date_time = date_time.replace(microsecond=0)
        return date_time.strftime(DTF)

    @classmethod
    def zero_seconds(cls, date_time):
        """
        Return the passed date_time with any seconds and microseconds set to 0.

        :param date_time:
        :type date_time: datetime or str
        :return:
        """
        if not (isinstance(date_time, datetime) or isinstance(date_time, str)):
            raise TypeError("Datetime or str required but {} was passed."
                            .format(type(date_time)))

        if isinstance(date_time, str):
            date_time = datetime.strptime(date_time, DTF)
            return date_time.strftime(DTF)
        return date_time.replace(second=0, microsecond=0)

    @classmethod
    def reformat_server_datetime_for_frontend(
            cls, date_time, date_first=False, two_character_year=False,
            context_with_timezone=None):
        """
        Reformat a datetime in Odoo's 'default server datetime format'
        (see imports) to one more appropriate for the front end.

        Can choose whether the date or time comes first and optionally convert
        to client timezone.

        :param date_time:
        :type date_time: str
        :param date_first:
        :type date_first: bool
        :param two_character_year:
        :type two_character_year: bool
        :param context_with_timezone: A record's context with a 'tz' key
        specifying the timezone of the current client.
        :type context_with_timezone: dict
        :return:
        :rtype: str
        """
        date_time = cls.zero_seconds(date_time)
        date_time = datetime.strptime(date_time, DTF)

        time_format = cls.time_format_front_end
        date_format = cls.date_format_front_end
        if two_character_year:
            date_format = cls.date_format_front_end_two_character_year

        if date_first:
            datetime_format = cls.format_string.format(date_format,
                                                       time_format)
        else:
            datetime_format = cls.format_string.format(time_format,
                                                       date_format)

        if context_with_timezone:
            cls._context = context_with_timezone
            date_time = Datetime.context_timestamp(cls, date_time)
        date_time = date_time.strftime(datetime_format)
        return date_time

    def validate_and_convert(self, date_time):
        if not isinstance(date_time, str) \
                and not isinstance(date_time, datetime):
            raise TypeError(
                "Passed datetime must either be a string or datetime object."
            )
        if isinstance(date_time, str):
            date_time = self.parse_datetime_str_from_known_format(date_time)
        return date_time

    @classmethod
    def parse_datetime_str_from_known_format(cls, date_time):
        for datetime_format in cls.known_formats:
            try:
                date_time = datetime.strptime(date_time, datetime_format)
                return date_time
            except ValueError:
                pass
        raise ValueError(
            "Passed datetime string {} does not match any format known to be "
            "used within the system.".format(date_time)
        )

    @classmethod
    def convert_datetime_str_to_known_format(cls, datetime_str,
                                             datetime_format):
        if datetime_format not in cls.known_formats:
            raise ValueError(
                "Passed datetime format {} does not match any format known to "
                "be used within the system.".format(datetime_format)
            )
        return cls.convert_datetime_str_to_format(datetime_str,
                                                  datetime_format)

    @classmethod
    def convert_datetime_str_to_format(cls, datetime_str, datetime_format):
        date_time = cls.parse_datetime_str_from_known_format(datetime_str)
        datetime_str = date_time.strftime(datetime_format)
        return datetime_str

    @classmethod
    def get_current_time(cls, as_string=False):
        """
        Get the current time. Making this a separate function makes it easier
        to patch.

        :param as_string: Should return datetime as string
        :return: datetime or string representation of datetime
        """
        current_datetime = datetime.now()
        if as_string:
            return datetime.strftime(current_datetime, DTF)
        return current_datetime

    @api.model
    def get_localised_time(self, date_time=None, return_string=None,
                           return_string_format=None):
        """
        Get the localised time for datetime.now() or passed datetime.
        :param date_time: str
        :return: Datetime in client timezone.
        :rtype: datetime or str
        """
        if date_time is None:
            date_time = self.get_current_time()
        date_time = self.validate_and_convert(date_time)

        date_time = fields.datetime.context_timestamp(
            self._cr, self._uid, date_time, self._context)

        if return_string:
            if return_string_format is None:
                return_string_format = DTF
            date_time = date_time.strftime(return_string_format)
        return date_time
