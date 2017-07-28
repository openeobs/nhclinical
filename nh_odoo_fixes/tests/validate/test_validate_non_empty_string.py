from openerp.tests.common import TransactionCase
from openerp.addons.nh_odoo_fixes.validate import validate_non_empty_string


class TestValidateNonEmptyString(TransactionCase):
    """ Test validation of strings not being empty """

    def test_string_is_none(self):
        """ Test that returns False when string is None """
        self.assertFalse(validate_non_empty_string(None))

    def test_string_is_false(self):
        """ Test that returns False when string is False """
        self.assertFalse(validate_non_empty_string(False))

    def test_string_is_spaces(self):
        """ TEst that returns False when string is ' ' """
        self.assertFalse(validate_non_empty_string(' '))

    def test_string_is_tabs(self):
        """ Test that returns False when string is '    ' """
        self.assertFalse(validate_non_empty_string('    '))

    def test_string_is_int(self):
        """ Test doesn't blow up when string is non-string such as int """
        self.assertTrue(validate_non_empty_string(1337))

    def test_string_has_value(self):
        """ Test that returns True when string has a value """
        self.assertTrue(validate_non_empty_string('Colin is awesome'))
