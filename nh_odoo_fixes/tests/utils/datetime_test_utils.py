# -*- coding: utf-8 -*-
from openerp import models


class DatetimeTestUtils(models.AbstractModel):
    """
    Contains useful methods for tests involving datetimes.
    """
    _name = 'datetime_test_utils'

    def assert_datetimes_equal_disregarding_seconds(self, expected, actual):
        """
        Useful for asserting that datetimes are within 1 minute of each other.

        :param expected:
        :param actual:
        :return:
        """
        datetime_utils = self.env['datetime_utils']
        expected = datetime_utils.zero_seconds(expected)
        actual = datetime_utils.zero_seconds(actual)
        if not expected == actual:
            raise AssertionError("Expected datetime '{}' is not equal to "
                                 "actual datetime '{}'.")
