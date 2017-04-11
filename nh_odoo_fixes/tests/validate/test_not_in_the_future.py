# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from openerp.addons.nh_odoo_fixes import validate
from openerp.exceptions import ValidationError
from openerp.tests.common import TransactionCase
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class TestNotInTheFuture(TransactionCase):
    """
    Tests the :method:`validate.not_in_the_future` method.
    """
    @staticmethod
    def test_now_does_not_raise_exception_with_datetime():
        validate.not_in_the_future(datetime.now())

    @staticmethod
    def test_now_does_not_raise_exception_with_string():
        validate.not_in_the_future(datetime.now().strftime(DTF))

    def test_one_second_in_the_future_does_raise_exception_with_datetime(self):
        with self.assertRaises(ValidationError):
            validate.not_in_the_future(datetime.now() + timedelta(seconds=1))

    def test_one_second_in_the_future_does_raise_exception_with_string(self):
        with self.assertRaises(ValidationError):
            date_time = (datetime.now() + timedelta(seconds=1)).strftime(DTF)
            validate.not_in_the_future(date_time)

    @staticmethod
    def test_before_1900_with_datetime_does_not_raise_exception():
        validate.not_in_the_future(datetime(year=1899, month=6, day=6))

    def test_before_1900_with_string_raises_exception(self):
        with self.assertRaises(ValueError):
            date_time = datetime(year=1899, month=6, day=6).strftime(DTF)
            validate.not_in_the_future(date_time)

    def test_passing_none(self):
        with self.assertRaises(TypeError):
            validate.not_in_the_future(None)

    def test_passing_false(self):
        with self.assertRaises(TypeError):
            validate.not_in_the_future(False)

    def test_string_not_in_correct_date_format(self):
        with self.assertRaises(ValueError):
            validate.not_in_the_future('Narnteenth uv Septembah')
