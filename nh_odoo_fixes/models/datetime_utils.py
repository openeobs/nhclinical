# -*- coding: utf-8 -*-
from datetime import datetime

from openerp import models
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class DatetimeUtils(models.AbstractModel):

    _name = 'datetime_utils'

    @classmethod
    def zero_microseconds(cls, date_time):
        if isinstance(date_time, str):
            date_time_split = date_time.split('.')
            if len(date_time_split) > 2:
                raise ValueError(
                    "Datetime contains more than one period and so is not in "
                    "the expected format. Method will not work successfully "
                    "for other formats in its current state."
                )
            return date_time_split[0] # Omit microseconds after period.
        return date_time.replace(microsecond=0)

    @classmethod
    def zero_seconds(cls, date_time):
        return date_time.replace(second=0, microsecond=0)

    @classmethod
    def reformat_server_datetime_for_frontend(cls, date_time):
        date_time = cls.zero_microseconds(date_time)
        first_refusal_date = datetime.strptime(date_time, DTF)
        datetime_format = '%d/%m/%Y %H:%M'
        first_refusal_date = first_refusal_date.strftime(datetime_format)
        return first_refusal_date
