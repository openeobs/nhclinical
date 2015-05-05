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

    def test_get_fullname(self):
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

    def test_get_name(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Family, middle and given names are present in record.
        patient_id = self.patient_pool.create(cr, uid, {
            'other_identifier': 'TESTHN001', 'given_name': 'John',
            'family_name': 'Smith', 'middle_names': 'Clarke'})
        result = self.patient_pool._get_name(cr, uid, [patient_id], fn=None, args=None)
        self.assertEquals('Smith, John Clarke', result[patient_id])

        # Scenario 2: Only one name field is present in record.
        patient_id_1 = self.patient_pool.create(cr, uid, {
            'other_identifier': 'TESTHN001', 'given_name': 'John'})
        result = self.patient_pool._get_name(cr, uid, [patient_id_1], fn=None, args=None)
        self.assertEquals(', John', result[patient_id_1])

        # Scenario 3: No names are present in patient record.
        patient_id_2 = self.patient_pool.create(cr, uid, {'other_identifier': 'TESTHN001'})
        result = self.patient_pool._get_name(cr, uid, [patient_id_2], fn=None, args=None)
        self.assertEquals(',', result[patient_id_2])

    def test_check_hospital_number(self):
        cr, uid = self.cr, self.uid
        self.patient_pool.create(cr, uid, {'other_identifier': 'TESTHN001'})

        # Scenario 1: if exception is False and hospital_number is correct.
        result = self.patient_pool.check_hospital_number(cr, uid, 'TESTHN001')
        self.assertTrue(result)

        # Scenario 2: if exception is False and hospital_number is incorrect.
        result = self.patient_pool.check_hospital_number(cr, uid, 'TESTHN002')
        self.assertFalse(result)

        # Scenario 3: if exception is True and hospital_number is correct.
        with self.assertRaises(except_orm):
            self.patient_pool.check_hospital_number(cr, uid, 'TESTHN001', exception='True')

        # Scenario 4: if exception is False and hospital_number is incorrect.
        with self.assertRaises(except_orm):
            self.patient_pool.check_hospital_number(cr, uid, 'TESTHN002', exception='False')

    def test_check_nhs_number(self):
        cr, uid = self.cr, self.uid
        self.patient_pool.create(cr, uid, {
            'other_identifier': 'TESTHN001', 'patient_identifier': 'TESTPI001'})

        # Scenario 1: if exception is False and nhs_number is correct.
        result = self.patient_pool.check_nhs_number(cr, uid, 'TESTPI001')
        self.assertTrue(result)

        # Scenario 2: if exception is False and nhs_number is incorrect.
        result = self.patient_pool.check_nhs_number(cr, uid, 'TESTPI002')
        self.assertFalse(result)

        # Scenario 3: if exception is True and nhs_number is correct.
        with self.assertRaises(except_orm):
            self.patient_pool.check_nhs_number(cr, uid, 'TESTPI001', exception=True)

        # Scenario 4: if exception is True and nhs_number is incorrect.
        with self.assertRaises(except_orm):
            self.patient_pool.check_nhs_number(cr, uid, 'TESTPI002', exception=True)

    def test_create(self):
        cr, uid = self.cr, self.uid

        patient_id = self.patient_pool.create(cr, uid, {'other_identifier': 'TESTHN001'})
        patient = self.patient_pool.browse(cr, uid, [patient_id])
        self.assertEquals(patient_id, patient.id)
        self.assertEquals('TESTHN001', patient.other_identifier)

        # test for when 'name' is not in vals
        self.assertEquals(',', patient.name)

        # test for that a partner is created in res_partner.
        self.assertEquals(patient_id, self.partner_pool.browse(cr, uid, [patient_id]).id)

        # test when 'name' is in vals
        patient_id = self.patient_pool.create(cr, uid, {'other_identifier': 'TESTHN001', 'name': 'Smith, John'})
        patient = self.patient_pool.browse(cr, uid, [patient_id])
        self.assertEquals('Smith, John', patient.name)

    def test_unlink(self):
        cr, uid = self.cr, self.uid

        patient_id = self.patient_pool.create(cr, uid, {'other_identifier': 'TEST_UNLINK'})
        self.patient_pool.unlink(cr, uid, [patient_id])
        # unlink sets the field 'active' to False, making it invisible to users
        self.assertFalse(self.patient_pool.browse(cr, uid, [patient_id]).active)







