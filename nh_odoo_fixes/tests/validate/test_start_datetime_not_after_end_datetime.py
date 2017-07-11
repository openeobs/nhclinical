# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from openerp.addons.nh_odoo_fixes import validate
from openerp.exceptions import ValidationError
from openerp.tests.common import TransactionCase
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class TestStartDatetimeNotAfterEndDatetime(TransactionCase):
    """
    Tests the :method:`validate.start_datetime_not_after_end_datetime` method.
    """
    @staticmethod
    def now():
        return datetime.now()

    @staticmethod
    def one_second_ago():
        return datetime.now() - timedelta(seconds=1)

    def test_start_datetime_before_end_datetime_does_not_raise_exception(self):
        start_datetime = self.one_second_ago()
        end_datetime = self.now()
        validate.start_datetime_not_after_end_datetime(
            start_datetime, end_datetime
        )

    def test_start_before_end_with_strings(self):
        start_datetime_string = self.one_second_ago().strftime(DTF)
        end_datetime_string = self.now().strftime(DTF)
        validate.start_datetime_not_after_end_datetime(
            start_datetime_string,
            end_datetime_string
        )

    def test_end_datetime_before_start_datetime_raises_exception(self):
        with self.assertRaises(ValidationError):
            start_datetime = self.now()
            end_datetime = self.one_second_ago()
            validate.start_datetime_not_after_end_datetime(
                start_datetime,
                end_datetime
            )

    def test_equal_start_and_end_date_does_not_raise_exception(self):
        start_datetime = self.one_second_ago()
        end_datetime = self.one_second_ago()
        validate.start_datetime_not_after_end_datetime(
            start_datetime,
            end_datetime
        )

    @staticmethod
    def test_before_1900_with_datetime_does_not_raise_exception():
        start_datetime = datetime(year=1899, month=6, day=6)
        end_datetime = datetime(year=1899, month=6, day=7)
        validate.start_datetime_not_after_end_datetime(
            start_datetime, end_datetime
        )

    def test_before_1900_with_string_raises_exception(self):
        with self.assertRaises(ValueError):
            start_datetime_string = \
                datetime(year=1899, month=6, day=6).strftime(DTF)
            end_datetime_string = \
                datetime(year=1899, month=6, day=7).strftime(DTF)
            validate.start_datetime_not_after_end_datetime(
                start_datetime_string, end_datetime_string
            )

    def test_passing_none(self):
        with self.assertRaises(TypeError):
            validate.start_datetime_not_after_end_datetime(None)

    def test_passing_false(self):
        with self.assertRaises(TypeError):
            validate.start_datetime_not_after_end_datetime(False)

    def test_string_not_in_correct_date_format(self):
        with self.assertRaises(ValueError):
            bad_format = 'Narnteenth uv Septembah'
            validate.start_datetime_not_after_end_datetime(
                bad_format, bad_format
            )
