# -*- coding: utf-8 -*-
"""Contains various useful methods for managing datetimes."""
from datetime import datetime

from openerp import models
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class DatetimeUtils(models.AbstractModel):

    _name = 'datetime_utils'

    date_format = '%d/%m/%Y'
    time_format = '%H:%M'
    format_string = '{} {}'

    @classmethod
    def zero_microseconds(cls, date_time):
        """
        Return the passed date_time with any microseconds set to 0.

        :param date_time:
        :type date_time: datetime or str
        :return:
        """
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
        :type date_time: datetime
        :return:
        """
        if not isinstance(date_time, datetime):
            raise TypeError("Datetime object required but {} was passed."
                            .format(type(date_time)))
        return date_time.replace(second=0, microsecond=0)

    @classmethod
    def reformat_server_datetime_for_frontend(cls, date_time,
                                              date_first=False):
        """
        Reformat a datetime in Odoo's 'default server datetime format'
        (see imports) to one more appropriate for the front end.

        Can choose whether the date or time comes first.

        :param date_time:
        :type date_time: str
        :param date_first:
        :type date_first: bool
        :return:
        :rtype: str
        """
        date_time = cls.zero_microseconds(date_time)
        date_time = datetime.strptime(date_time, DTF)
        if date_first:
            datetime_format = cls.format_string.format(cls.date_format,
                                                       cls.time_format)
        else:
            datetime_format = cls.format_string.format(cls.time_format,
                                                       cls.date_format)
        date_time = date_time.strftime(datetime_format)
        return date_time
