# -*- coding: utf-8 -*-
from datetime import datetime

from openerp.tests.common import TransactionCase
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class TestGetLocalisedTime(TransactionCase):
    def setUp(self):
        super(TestGetLocalisedTime, self).setUp()
        self.datetime_utils = self.env['datetime_utils']

    def call_test(self, date_time, return_string=None):
        context = {'tz': 'UTC'}
        return self.datetime_utils.with_context(context).get_localised_time(
            date_time, return_string=return_string)

    def test_returns_str_when_return_string_argument_is_true(self):
        date_time = '2017-06-06 14:00:27'
        actual_datetime = self.call_test(date_time, return_string=True)

        self.assertTrue(isinstance(actual_datetime, str))

    def test_returns_same_whether_datetime_or_str_passed(self):
        datetime_str = '2017-06-06 14:00:27'
        datetime_obj = datetime.strptime(datetime_str, DTF)

        return_str_passed = self.call_test(datetime_str, return_string=True)
        return_obj_passed = self.call_test(datetime_obj, return_string=True)

        self.assertEqual(return_str_passed, return_obj_passed)

    def test_datetime_str_unchanged_when_localised_timezone_is_utc_0(self):
        expected_datetime = '2017-06-06 14:00:27'
        actual_datetime = self.call_test(expected_datetime, return_string=True)

        self.assertEqual(expected_datetime, actual_datetime)
