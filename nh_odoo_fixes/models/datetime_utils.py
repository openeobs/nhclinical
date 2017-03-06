# -*- coding: utf-8 -*-
"""Contains various useful methods for managing datetimes."""
from datetime import datetime

from openerp import models
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class DatetimeUtils(models.AbstractModel):

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
            cls, date_time, date_first=False, two_character_year=False
    ):
        """
        Reformat a datetime in Odoo's 'default server datetime format'
        (see imports) to one more appropriate for the front end.

        Can choose whether the date or time comes first.

        :param date_time:
        :type date_time: str
        :param date_first:
        :type date_first: bool
        :param two_character_year:
        :type two_character_year: bool
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
        date_time = cls.parse_datetime_str_from_known_format(datetime_str)
        datetime_str = date_time.strftime(datetime_format)
        return datetime_str
