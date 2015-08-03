import logging

from openerp.tests import common
from openerp.osv.orm import except_orm

_logger = logging.getLogger(__name__)


class TestClinicalPatient(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestClinicalPatient, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

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
        name = dict(family_name=None, given_name=None, middle_names=None)
        self.assertEquals(',', self.patient_pool._get_fullname(name))
        # False as argument
        name = dict(family_name=False, given_name='', middle_names='')
        self.assertEquals(',', self.patient_pool._get_fullname(name))
        # an empty dictionary creates name ','
        name = dict()
        self.assertEquals(',', self.patient_pool._get_fullname(name))

    def test_02_get_name(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Family, middle and given names are present in record.
        patient_id = self.patient_pool.create(cr, uid, {
            'other_identifier': 'TESTHN001', 'given_name': 'John',
            'family_name': 'Smith', 'middle_names': 'Clarke'})
        result = self.patient_pool._get_name(cr, uid, [patient_id], fn=None, args=None)
        self.assertEquals('Smith, John Clarke', result[patient_id])

        # Scenario 2: Only one name field is present in record.
        patient_id_1 = self.patient_pool.create(cr, uid, {
            'other_identifier': 'TESTHN002', 'given_name': 'John'})
        result = self.patient_pool._get_name(cr, uid, [patient_id_1], fn=None, args=None)
        self.assertEquals(', John', result[patient_id_1])

        # Scenario 3: No names are present in patient record.
        patient_id_2 = self.patient_pool.create(cr, uid, {'other_identifier': 'TESTHN003'})
        result = self.patient_pool._get_name(cr, uid, [patient_id_2], fn=None, args=None)
        self.assertEquals(',', result[patient_id_2])

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
            self.patient_pool.check_hospital_number(cr, uid, 'TESTHN001', exception='True')

        # Scenario 4: if exception is False and hospital_number is incorrect.
        with self.assertRaises(except_orm):
            self.patient_pool.check_hospital_number(cr, uid, 'TESTHN009', exception='False')

    def test_04_check_nhs_number(self):
        cr, uid = self.cr, self.uid
        self.patient_pool.create(cr, uid, {'patient_identifier': 'TESTPI001'})

        # Scenario 1: if exception is False and nhs_number is correct.
        result = self.patient_pool.check_nhs_number(cr, uid, 'TESTPI001')
        self.assertTrue(result)

        # Scenario 2: if exception is False and nhs_number is incorrect.
        result = self.patient_pool.check_nhs_number(cr, uid, 'TESTPI002')
        self.assertFalse(result)

        # Scenario 3: if exception is True and nhs_number is correct.
        with self.assertRaises(except_orm):
            self.patient_pool.check_nhs_number(cr, uid, 'TESTPI001', exception='True')

        # Scenario 4: if exception is True and nhs_number is incorrect.
        with self.assertRaises(except_orm):
            self.patient_pool.check_nhs_number(cr, uid, 'TESTPI002', exception='False')

    def test_05_create(self):
        cr, uid = self.cr, self.uid

        patient_id = self.patient_pool.create(cr, uid, {'other_identifier': 'TESTHN004'})
        patient = self.patient_pool.browse(cr, uid, [patient_id])
        self.assertEquals(patient_id, patient.id)
        self.assertEquals('TESTHN004', patient.other_identifier)

        # test for when 'name' is not in vals
        self.assertEquals(',', patient.name)

        # test for that a partner is created in res_partner.
        self.assertEquals(patient_id, self.partner_pool.browse(cr, uid, [patient_id]).id)

        # test when 'name' is in vals
        patient_id = self.patient_pool.create(cr, uid, {'other_identifier': 'TESTHN005', 'name': 'Smith, John'})
        patient = self.patient_pool.browse(cr, uid, [patient_id])
        self.assertEquals('Smith, John', patient.name)

    def test_06_unlink(self):
        cr, uid = self.cr, self.uid

        patient_id = self.patient_pool.create(cr, uid, {'other_identifier': 'TEST_UNLINK'})
        self.patient_pool.unlink(cr, uid, [patient_id])
        # unlink sets the field 'active' to False, making it invisible to users
        self.assertFalse(self.patient_pool.browse(cr, uid, [patient_id]).active)

    def test_07_check_data(self):
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
        data.update({'other_identifier': 'TESTHN009', 'patient_identifier': 'TESTPI001'})
        with self.assertRaises(except_orm):
            self.patient_pool.check_data(cr, uid, data)

        # Scenario 4: Correct create data with title
        data.update({'patient_identifier': 'TESTNHS09', 'title': 'Mr.'})
        self.assertTrue(self.patient_pool.check_data(cr, uid, data))
        self.assertTrue(isinstance(data.get('title'), int))

        # Scenario 5: Update data, no existing patient with Hospital Number or NHS Number
        data.update({'other_identifier': 'TESTHN008', 'patient_identifier': 'TESTNHS08'})
        with self.assertRaises(except_orm):
            self.patient_pool.check_data(cr, uid, data, create=False)

        # Scenario 6: Update data, no existing patient with Hospital Number
        data.update({'other_identifier': 'TESTHN008'})
        with self.assertRaises(except_orm):
            self.patient_pool.check_data(cr, uid, data, create=False)
        self.assertFalse(self.patient_pool.check_data(cr, uid, data, create=False, exception=False))

        # Scenario 7: Update data, no existing patient with NHS Number
        data.update({'patient_identifier': 'TESTNHS08'})
        with self.assertRaises(except_orm):
            self.patient_pool.check_data(cr, uid, data, create=False)
        self.assertFalse(self.patient_pool.check_data(cr, uid, data, create=False, exception=False))

        # Scenario 8: Update data, 2 identifiers for 2 different patients
        data.update({'other_identifier': 'TESTHN001', 'patient_identifier': 'TESTPI001'})
        with self.assertRaises(except_orm):
            self.patient_pool.check_data(cr, uid, data, create=False)
        self.assertFalse(self.patient_pool.check_data(cr, uid, data, create=False, exception=False))

        # Scenario 9: Correct update data
        data.update({'other_identifier': 'TESTHN009'})
        self.assertTrue(self.patient_pool.check_data(cr, uid, data, create=False))
        self.assertTrue(data.get('patient_id'))