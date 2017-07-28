# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase
from openerp.osv.osv import except_orm


class TestCheckIdentifierForBadChars(TransactionCase):
    """ Test that we can raise errors when bad characters are in a string """

    def setUp(self):
        super(TestCheckIdentifierForBadChars, self).setUp()
        self.patient_model = self.env['nh.clinical.patient']

    def test_raises_on_bad_character(self):
        """ Test that an exception is raised on bad character in string """
        with self.assertRaises(except_orm) as error:
            self.patient_model._check_identifier_for_bad_chars('"£%£%%"£$"£')
        self.assertEqual(
            error.exception.value,
            'Patient identifier can only contain '
            'alphanumeric characters, hyphens and underscores'
        )

    def test_good_characters(self):
        """ Test that doesn't raise on good characters in string """
        self.patient_model._check_identifier_for_bad_chars('this is ok')
