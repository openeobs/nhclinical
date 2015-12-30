# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestPatientRegister(TransactionCase):

    def setUp(self):
        super(TestPatientRegister, self).setUp()
        cr, uid = self.cr, self.uid
        self.activity_pool = self.registry('nh.activity')
        self.patient_pool = self.registry('nh.clinical.patient')
        self.location_pool = self.registry('nh.clinical.location')
        self.api = self.registry('nh.clinical.api')
        self.register_pool = self.registry('nh.clinical.adt.patient.register')
        self.user_pool = self.registry('res.users')

        self.adt_uid = self.user_pool.search(
            cr, uid, [['login', '=', 'adt']])[0]

    def test_api_register_using_hospital_number_creates_patient(self):
        cr, uid = self.cr, self.uid
        patient_data = {
            'family_name': "Fname",
            'given_name': 'Gname',
            'dob': '1988-08-14 18:00:00',
            'gender': 'M',
            'sex': 'M'
        }

        self.api.register(cr, self.adt_uid, 'TESTP0001', patient_data)

        patient_id = self.patient_pool.search(
            cr, uid, [('other_identifier', '=', 'TESTP0001')])
        self.assertTrue(patient_id, msg="Patient was not created")
        # creates and completes a 'nh.clinical.adt.patient.register' activity
        activity_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.adt.patient.register'],
            ['patient_id', '=', patient_id[0]]
        ])
        self.assertTrue(activity_id, msg="Register Activity not generated")
        activity = self.activity_pool.browse(cr, uid, activity_id[0])
        self.assertEqual(activity.state, 'completed')

    def test_api_register_using_NHS_number_creates_patient(self):
        cr, uid = self.cr, self.uid
        patient_data = {
            'patient_identifier': 'TESTNHS001',
            'family_name': "Fname2",
            'given_name': 'Gname2',
            'gender': 'F',
            'sex': 'F'
        }
        self.api.register(cr, self.adt_uid, '', patient_data)

        patient_id = self.patient_pool.search(
            cr, uid, [('patient_identifier', '=', 'TESTNHS001')])
        self.assertTrue(patient_id, msg="Patient was not created")
        # creates and completes a 'nh.clinical.adt.patient.register' activity
        activity_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.adt.patient.register'],
            ['patient_id', '=', patient_id[0]]
        ])
        self.assertTrue(activity_id, msg="Register Activity not generated")
        activity = self.activity_pool.browse(cr, uid, activity_id[0])
        self.assertEqual(activity.state, 'completed')

    def test_adt_patient_register_using_hospital_number_creates_patient(self):
        cr, uid = self.cr, self.uid
        register_data = {
            'family_name': 'Family',
            'middle_names': 'Middle',
            'given_name': 'Given',
            'other_identifier': 'TEST001',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }

        register_activity_id = self.register_pool.create_activity(
            cr, self.adt_uid, {}, {})
        self.activity_pool.submit(cr, self.adt_uid, register_activity_id,
                                  register_data)
        patient_id = self.activity_pool.complete(cr, self.adt_uid,
                                                 register_activity_id)

        self.assertTrue(patient_id,
                        msg="Patient Register: patient id not returned")
        patient_data = self.patient_pool.read(
            cr, uid, patient_id, ['family_name', 'given_name',
                                  'other_identifier', 'dob', 'gender', 'sex'])
        self.assertEqual(register_data['family_name'],
                         patient_data['family_name'],
                         msg="Patient Register: wrong patient data registered")
        self.assertEqual(register_data['given_name'],
                         patient_data['given_name'],
                         msg="Patient Register: wrong patient data registered")
        self.assertEqual(register_data['other_identifier'],
                         patient_data['other_identifier'],
                         msg="Patient Register: wrong patient data registered")
        self.assertEqual(register_data['dob'],
                         patient_data['dob'],
                         msg="Patient Register: wrong patient data registered")
        self.assertEqual(register_data['gender'],
                         patient_data['gender'],
                         msg="Patient Register: wrong patient data registered")
        self.assertEqual(register_data['sex'],
                         patient_data['sex'],
                         msg="Patient Register: wrong patient data registered")

    def test_adt_patient_register_using_NHS_number_creates_patient(self):
        cr = self.cr
        register_data = {
            'family_name': 'Family',
            'given_name': 'Given',
            'patient_identifier': 'TEST001',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }

        register_activity_id = self.register_pool.create_activity(
            cr, self.adt_uid, {}, {})
        self.activity_pool.submit(
            cr, self.adt_uid, register_activity_id, register_data)
        patient_id = self.activity_pool.complete(
            cr, self.adt_uid, register_activity_id)
        self.assertTrue(patient_id,
                        msg="Patient Register: patient id not returned")

    def test_adt_patient_register_creates_patient_using_hosp_and_NHS_num(self):
        cr = self.cr
        register_data = {
            'family_name': 'Family',
            'given_name': 'Given',
            'patient_identifier': 'TEST001',
            'other_identifier': 'TEST001',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }
        register_activity_id = self.register_pool.create_activity(
            cr, self.adt_uid, {}, {})
        self.activity_pool.submit(
            cr, self.adt_uid, register_activity_id, register_data)
        patient_id = self.activity_pool.complete(
            cr, self.adt_uid, register_activity_id)
        self.assertTrue(patient_id,
                        msg="Patient Register: patient id not returned")

    def test_adt_create_activity_exception_if_patient_already_registered(self):
        # Patient with same other_identifier already registered
        # (see data/patients.xml)
        register_data = {
            'family_name': 'Doe',
            'given_name': 'John',
            'other_identifier': 'HOSNUM0000',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }

        with self.assertRaises(except_orm):
            self.register_pool.create_activity(self.cr, self.adt_uid, {},
                                               register_data)

    def test_adt_patient_register_raises_except_with_registered_patient(self):
        cr = self.cr
        # Patient with same other_identifier is ALREADY registered
        # (see data/patients.xml)
        register_data = {
            'family_name': 'Doe',
            'given_name': 'John',
            'other_identifier': 'HOSNUM0000',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }

        register_activity_id = self.register_pool.create_activity(
            cr, self.adt_uid, {}, {})
        with self.assertRaises(except_orm):
            self.activity_pool.submit(cr, self.adt_uid, register_activity_id,
                                      register_data)
