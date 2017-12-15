# -*- coding: utf-8 -*-
"""
Module containing the TestInMinMaxRange class.
"""
from openerp.addons.nh_odoo_fixes import validate
from openerp.exceptions import ValidationError
from openerp.tests.common import SingleTransactionCase


class TestInMinMaxRange(SingleTransactionCase):
    """
    Tests for the `in_min_max_range` method of the `validate.py` module.
    """
    @staticmethod
    def call_test(value, minimum, maximum):
        """
        Call the method under test.

        :param value: Any value of any type that should be in between or equal
            to the minimum and maximum.
        :param minimum: The value cannot be below this.
        :param maximum: The value cannot be above this.
        """
        validate.in_min_max_range(minimum, maximum, value)

    def test_value_inside_of_range(self):
        self.call_test(value=2, minimum=1, maximum=3)

    def test_negative_value_inside_range(self):
        self.call_test(value=-5, minimum=-10, maximum=-1)

    def test_raises_if_value_below_minimum(self):
        with self.assertRaises(ValidationError):
            self.call_test(value=1, minimum=2, maximum=3)

    def test_raises_if_negative_value_below_negative_minimum(self):
        with self.assertRaises(ValidationError):
            self.call_test(value=-5, minimum=-2, maximum=-1)

    def test_raises_if_zero_value_below_minimum(self):
        with self.assertRaises(ValidationError):
            self.call_test(value=0, minimum=1, maximum=5)

    def test_raises_if_value_above_maximum(self):
        with self.assertRaises(ValidationError):
            self.call_test(value=3, minimum=1, maximum=2)

    def test_raises_if_negative_value_above_maximum(self):
        with self.assertRaises(ValidationError):
            self.call_test(value=-1, minimum=-3, maximum=-2)

    def test_raises_if_zero_value_above_maximum(self):
        with self.assertRaises(ValidationError):
            self.call_test(value=0, minimum=-2, maximum=-1)

    def test_does_not_raise_if_value_on_minimum(self):
        self.call_test(value=1, minimum=1, maximum=2)

    def test_does_not_raise_if_value_on_maximum(self):
        self.call_test(value=2, minimum=1, maximum=2)

    def test_does_not_raise_if_all_args_are_equal(self):
        self.call_test(value=1, minimum=1, maximum=1)

    def test_can_compare_non_int_types(self):
        """
        As this is a duck typing language, the caller should be able to pass
        anything with an awareness of the `__eq__` method behaviour of that
        type.
        """
        self.call_test(value='b', minimum='a', maximum='z')
