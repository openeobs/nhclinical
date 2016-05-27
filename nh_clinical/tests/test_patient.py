# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import logging

from openerp.tests import common
from openerp.osv.orm import except_orm

_logger = logging.getLogger(__name__)


class TestClinicalPatient(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestClinicalPatient, cls).setUpClass()
        cls.patient_pool = cls.registry('nh.clinical.patient')
        cls.partner_pool = cls.registry('res.partner')

    def test_01_get_fullname(self):
        # family, given and middle names
        name = dict(family_name='Smith', given_name='John',
                    middle_names='Clarke')
        self.assertEquals('Smith, John Clarke',
                          self.patient_pool._get_fullname(name))
        # family, given, no middle
        name = dict(family_name='Smith', given_name='John', middle_names='')
        self.assertEquals(
            'Smith, John', self.patient_pool._get_fullname(name))
        # family and middle, no given name
        name = dict(family_name='Smith', given_name='', middle_names='Clarke')
        self.assertEquals(
            'Smith, Clarke', self.patient_pool._get_fullname(name))
        # family name only
        name = dict(family_name='Smith', given_name='', middle_names='')
        self.assertEquals(
            'Smith,', self.patient_pool._get_fullname(name))
        # no family, given and middle names only
        name = dict(family_name='', given_name='John', middle_names='Clarke')
        self.assertEqual(
            ', John Clarke', self.patient_pool._get_fullname(name))
        # given name only
        name = dict(family_name='', given_name='John', middle_names='')
        self.assertEquals(
            ', John', self.patient_pool._get_fullname(name))
        # middle names only
        name = dict(family_name='', given_name='', middle_names='Clarke')
        self.assertEquals(
            ', Clarke', self.patient_pool._get_fullname(name))
        # no names
        name = dict(family_name='', given_name='', middle_names='')
        self.assertEquals(',', self.patient_pool._get_fullname(name))
        # None as argument
        with self.assertRaises(except_orm):
            name = dict(family_name=None, given_name=None, middle_names=None)
            self.patient_pool._get_fullname(name)
        # False as argument
        with self.assertRaises(except_orm):
            name = dict(family_name=False, given_name='', middle_names='')
            self.assertEquals(',', self.patient_pool._get_fullname(name))
        # an empty dictionary creates name ','
        with self.assertRaises(except_orm):
            name = dict()
            self.assertEquals(',', self.patient_pool._get_fullname(name))

    def test_none_middle_name_not_none(self):
        name = dict(family_name='Smith', given_name='John',
                    middle_names=None)
        self.assertEquals('Smith, John',
                          self.patient_pool._get_fullname(name))

    def test_false_middle_name_not_false(self):
        name = dict(family_name='Smith', given_name='John',
                    middle_names=False)
        self.assertEquals('Smith, John',
                          self.patient_pool._get_fullname(name))

    def test_02_get_name(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Family, middle and given names are present in record.
        patient_id = self.patient_pool.create(cr, uid, {
            'other_identifier': 'TESTHN001', 'given_name': 'John',
            'family_name': 'Smith', 'middle_names': 'Clarke'})
        result = self.patient_pool._get_name(cr, uid, [patient_id], fn=None,
                                             args=None)
        self.assertEquals('Smith, John Clarke', result[patient_id])

    def test_02_get_name_with_firstname(self):
        cr, uid = self.cr, self.uid
        with self.assertRaises(except_orm):
            patient_id_1 = self.patient_pool.create(cr, uid, {
                'other_identifier': 'TESTHN002', 'given_name': 'John'})
            self.patient_pool._get_name(
                cr, uid, [patient_id_1], fn=None, args=None)

    def test_02_get_name_with_no_name(self):
        cr, uid = self.cr, self.uid
        with self.assertRaises(except_orm):
            patient_id_2 = self.patient_pool.create(
                cr, uid, {'other_identifier': 'TESTHN003'})
            self.patient_pool._get_name(
                cr, uid, [patient_id_2], fn=None, args=None)

    def test_03_check_hospital_number(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: if exception is False and hospital_number is correct.
        result = self.patient_pool.check_hospital_number(cr, uid, 'TESTHN001')
        self.assertTrue(result)

        # Scenario 2: if exception is False and hospital_number is incorrect.
        result = self.patient_pool.check_hospital_number(cr, uid, 'TESTHN009')
        self.assertFalse(result)

        # Scenario 3: if exception is True and hospital_number is correct.
        with self.assertRaises(except_orm):
            self.patient_pool.check_hospital_number(cr, uid, 'TESTHN001',
                                                    exception='True')

        # Scenario 4: if exception is False and hospital_number is incorrect.
        with self.assertRaises(except_orm):
            self.patient_pool.check_hospital_number(cr, uid, 'TESTHN009',
                                                    exception='False')

    def test_04_check_nhs_number(self):
        cr, uid = self.cr, self.uid
        self.patient_pool.create(cr, uid, {
            'patient_identifier': 'TESTPI001',
            'given_name': 'John',
            'family_name': 'Smith',
            'middle_names': 'Clarke'})

        # Scenario 1: if exception is False and nhs_number is correct.
        result = self.patient_pool.check_nhs_number(cr, uid, 'TESTPI001')
        self.assertTrue(result)

        # Scenario 2: if exception is False and nhs_number is incorrect.
        result = self.patient_pool.check_nhs_number(cr, uid, 'TESTPI002')
        self.assertFalse(result)

        # Scenario 3: if exception is True and nhs_number is correct.
        with self.assertRaises(except_orm):
            self.patient_pool.check_nhs_number(cr, uid, 'TESTPI001',
                                               exception='True')

        # Scenario 4: if exception is True and nhs_number is incorrect.
        with self.assertRaises(except_orm):
            self.patient_pool.check_nhs_number(cr, uid, 'TESTPI002',
                                               exception='False')

    def test_05_create(self):
        cr, uid = self.cr, self.uid

        patient_id = self.patient_pool.create(
            cr, uid, {'other_identifier': 'TESTHN004', 'given_name': 'John',
                      'family_name': 'Smith', 'middle_names': 'Clarke'})
        patient = self.patient_pool.browse(cr, uid, [patient_id])
        self.assertEquals(patient_id, patient.id)
        self.assertEquals('TESTHN004', patient.other_identifier)

        # test for that a partner is created in res_partner.
        self.assertEquals(patient_id,
                          self.partner_pool.browse(cr, uid, [patient_id]).id)

        # test when 'name' is in vals
        patient_id = self.patient_pool.create(
            cr, uid, {'other_identifier': 'TESTHN005', 'name': 'Smith, John'})
        patient = self.patient_pool.browse(cr, uid, [patient_id])
        self.assertEquals('Smith, John', patient.name)

    def test_06_write(self):
        cr, uid = self.cr, self.uid

        patient_id = self.patient_pool.search(
            cr, uid, [['other_identifier', '=', 'TESTHN004']])
        self.assertTrue(self.patient_pool.write(cr, uid, patient_id,
                                                {'title': 'test'}))
        self.assertTrue(self.patient_pool.write(cr, uid, patient_id,
                                                {'family_name': 'testfamily'}))

    def test_07_unlink(self):
        cr, uid = self.cr, self.uid

        patient_id = self.patient_pool.create(
            cr, uid, {'other_identifier': 'TEST_UNLINK', 'given_name': 'John',
                      'family_name': 'Smith', 'middle_names': 'Clarke'})
        self.patient_pool.unlink(cr, uid, [patient_id])
        # unlink sets the field 'active' to False, making it invisible to users
        self.assertFalse(
            self.patient_pool.browse(cr, uid, [patient_id]).active)

    def test_08_check_data(self):
        cr, uid = self.cr, self.uid

        data = {
            'family_name': 'Family',
            'given_name': 'Given',
            'middle_names': 'Middle Names',
            'dob': '2000-01-01 00:00:00',
            'sex': 'U',
            'gender': 'U',
            'ethnicity': 'Z'
        }

        # Scenario 1: Data without Hospital number and NHS number
        with self.assertRaises(except_orm):
            self.patient_pool.check_data(cr, uid, data)

        # Scenario 2: Data with an existing Hospital number
        data.update({'other_identifier': 'TESTHN001'})
        with self.assertRaises(except_orm):
            self.patient_pool.check_data(cr, uid, data)

        # Scenario 3: Data with an existing NHS number
        data.update({'other_identifier': 'TESTHN009',
                     'patient_identifier': 'TESTPI001'})
        with self.assertRaises(except_orm):
            self.patient_pool.check_data(cr, uid, data)

        # Scenario 4: Correct create data with title
        data.update({'patient_identifier': 'TESTNHS09', 'title': 'Mr.'})
        self.assertTrue(self.patient_pool.check_data(cr, uid, data))
        self.assertTrue(isinstance(data.get('title'), int))

        # Scenario 5:
        # Update data, no existing patient with Hospital Number or NHS Number.
        data.update({'other_identifier': 'TESTHN008',
                     'patient_identifier': 'TESTNHS08'})
        with self.assertRaises(except_orm):
            self.patient_pool.check_data(cr, uid, data, create=False)

        # Scenario 6: Update data, no existing patient with Hospital Number
        data.update({'other_identifier': 'TESTHN008'})
        with self.assertRaises(except_orm):
            self.patient_pool.check_data(cr, uid, data, create=False)
        self.assertFalse(self.patient_pool.check_data(
            cr, uid, data, create=False, exception=False))

        # Scenario 7: Update data, no existing patient with NHS Number
        data.update({'patient_identifier': 'TESTNHS08'})
        with self.assertRaises(except_orm):
            self.patient_pool.check_data(cr, uid, data, create=False)
        self.assertFalse(self.patient_pool.check_data(
            cr, uid, data, create=False, exception=False))

        # Scenario 8: Update data, 2 identifiers for 2 different patients
        data.update({'other_identifier': 'TESTHN001',
                     'patient_identifier': 'TESTPI001'})
        with self.assertRaises(except_orm):
            self.patient_pool.check_data(cr, uid, data, create=False)
        self.assertFalse(self.patient_pool.check_data(
            cr, uid, data, create=False, exception=False))

        # Scenario 9: Correct update data
        data.update({'other_identifier': 'TESTHN009'})
        self.assertTrue(self.patient_pool.check_data(cr, uid, data,
                                                     create=False))
        self.assertTrue(data.get('patient_id'))

    def test_get_not_admitted_patient_ids_gets_patients_no_started_spell(self):
        cr, uid = self.cr, self.uid
        spell_pool = self.registry('nh.clinical.spell')
        patient_id = self.patient_pool.create(
            cr, uid, {'other_identifier': 'TESTHN010', 'given_name': 'John',
                      'family_name': 'Smith', 'middle_names': 'Clarke'})

        patient_ids = self.patient_pool.get_not_admitted_patient_ids(cr, uid)

        self.assertTrue(patient_id in patient_ids)
        spell_ids = spell_pool.search(
            cr, uid, [('patient_id', '=', patient_id)])
        self.assertEqual(len(spell_ids), 0)

    def test_not_admitted_dict_with_key_patient_id_and_value_True(self):
        cr, uid = self.cr, self.uid
        patient_id = self.patient_pool.create(
            cr, uid, {'other_identifier': 'TESTHN011', 'given_name': 'John',
                      'family_name': 'Smith', 'middle_names': 'Clarke'})

        res = self.patient_pool._not_admitted(
            cr, uid, [patient_id], None, None)

        self.assertEqual(res, {patient_id: True})

    def test_not_admitted_search_return_domain_patients_not_admitted(self):
        cr, uid = self.cr, self.uid
        patient_id = self.patient_pool.create(
            cr, uid, {'other_identifier': 'TESTHN012', 'given_name': 'John',
                      'family_name': 'Smith', 'middle_names': 'Clarke'})
        args = [('not_admitted', '=', True)]

        domain = self.patient_pool._not_admitted_search(
            cr, uid, None, None, args)

        self.assertEqual(type(domain), list)
        self.assertTrue(patient_id in domain[0][2])
