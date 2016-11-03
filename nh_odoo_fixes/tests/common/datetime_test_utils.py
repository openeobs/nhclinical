# -*- coding: utf-8 -*-
from unittest2 import TestCase

# Need to extend TestCase to make use of it's assertion methods.
class DatetimeTestUtils(TestCase):

    def runTest(self):
        pass # To keep TestCase.__init__() happy.

    @classmethod
    def zero_datetime_seconds(cls, date_time):
        return date_time.replace(second=0, microsecond=0)

    def assert_datetimes_equal_disregarding_seconds(self, expected, actual):
        expected = self.zero_datetime_seconds(expected)
        actual = self.zero_datetime_seconds(actual)
        self.assertEqual(expected, actual)
