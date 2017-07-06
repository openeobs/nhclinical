# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase


class TestCleanIdentifiers(TransactionCase):
    """ Test the _clean_identifiers method on the nh.clinical.patient model """

    def setUp(self):
        super(TestCleanIdentifiers, self).setUp()
        self.patient_model = self.env['nh.clinical.patient']
        self.test_vals = {
            'given_name': 'Test',
            'family_name': 'McTestersen'
        }

    def test_removes_spaces(self):
        """ Test that the method removes spaces from the identifiers """
        vals = self.test_vals.copy()
        vals['other_identifier'] = '     test   hospital   number'
        vals['patient_identifier'] = 'test                  nhs      number'
        clean_vals = self.patient_model._clean_identifiers(vals)
        self.assertEqual(clean_vals['other_identifier'], 'testhospitalnumber')
        self.assertEqual(clean_vals['patient_identifier'], 'testnhsnumber')

    def test_removes_non_alphanumeric(self):
        """ Test that the method removes non-alphanumeric characters """
        vals = self.test_vals.copy()
        vals['other_identifier'] = '`|!"£$%^&*()_+[]{}test:@~;\'<>' \
                                   '#hospital/?,.number'
        vals['patient_identifier'] = '¬`!"£!"test)(*&^!+_}{~@:?><nhs[];/number'
        clean_vals = self.patient_model._clean_identifiers(vals)
        self.assertEqual(clean_vals['other_identifier'], '_testhospitalnumber')
        self.assertEqual(clean_vals['patient_identifier'], 'test_nhsnumber')

    def test_doesnt_change_other_values(self):
        """ Test that the method doesn't remove other values in dictionary """
        vals = self.test_vals.copy()
        vals['other_identifier'] = '123'
        vals['patient_identifier'] = '123'
        clean_vals = self.patient_model._clean_identifiers(vals)
        self.assertEqual(clean_vals['other_identifier'], '123')
        self.assertEqual(clean_vals['patient_identifier'], '123')
        self.assertEqual(clean_vals['given_name'], 'Test')
        self.assertEqual(clean_vals['family_name'], 'McTestersen')

    def test_no_identifiers_present(self):
        """ Test doesn't blow up if there's no identifiers present in dict """
        clean_vals = self.patient_model._clean_identifiers(self.test_vals)
        self.assertEqual(clean_vals['given_name'], 'Test')
        self.assertEqual(clean_vals['family_name'], 'McTestersen')
