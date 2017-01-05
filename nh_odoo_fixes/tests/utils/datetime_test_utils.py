# -*- coding: utf-8 -*-
from unittest2 import TestCase


class DatetimeTestUtils(TestCase):
    """
    Contains useful methods for tests involving datetimes.
    Extends TestCase to make use of it's assertion methods.
    """
    def runTest(self):
        pass  # To keep TestCase.__init__() happy.

    def assert_datetimes_equal_disregarding_seconds(self, expected, actual):
        """
        Useful for asserting that datetimes are within 1 minute of each other.

        :param expected:
        :param actual:
        :return:
        """
        datetime_utils = self.env['datetime_utils']
        expected = datetime_utils.zero_datetime_seconds(expected)
        actual = datetime_utils.zero_datetime_seconds(actual)
        self.assertEqual(expected, actual)
