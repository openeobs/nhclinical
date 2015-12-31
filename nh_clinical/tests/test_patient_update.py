# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestPatientUpdate(TransactionCase):

    def setUp(self):
        super(TestPatientUpdate, self).setUp()
        cr, uid = self.cr, self.uid

        self.activity_pool = self.registry('nh.activity')
        self.patient_pool = self.registry('nh.clinical.patient')
        self.location_pool = self.registry('nh.clinical.location')
        self.api = self.registry('nh.clinical.api')
        self.register_pool = self.registry('nh.clinical.adt.patient.register')
        self.user_pool = self.registry('res.users')
        self.update_pool = self.registry('nh.clinical.adt.patient.update')

        self.adt_uid = self.user_pool.search(
            cr, uid, [['login', '=', 'adt']])[0]

    def test_api_update_using_hospital_number_updates_patient(self):
        cr, uid = self.cr, self.uid
        patient_data = {
            'family_name': "Fname0",
            'given_name': 'Gname0',
            'dob': '1988-08-14 18:00:00',
            'gender': 'M',
            'sex': 'M'
        }

        self.api.update(cr, self.adt_uid, 'HOSNUM0000', patient_data)

        patient_id = self.patient_pool.search(
            cr, uid, [('other_identifier', '=', 'HOSNUM0000')])[0]
        # creates and completes a 'nh.clinical.adt.patient.update' activity
        activity_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.adt.patient.update'],
            ['patient_id', '=', patient_id]
        ])
        self.assertTrue(activity_id, msg="Update Activity not generated")
        activity = self.activity_pool.browse(cr, uid, activity_id[0])
        self.assertEqual(activity.state, 'completed')

    def test_api_update_using_NHS_number_updates_patient(self):
        cr, uid = self.cr, self.uid
        patient_data = {
            'patient_identifier': 'NHSNUM0000',
            'family_name': "Fname20",
            'given_name': 'Gname20',
            'dob': '1988-08-14 18:00:00',
            'gender': 'F',
            'sex': 'F'
        }

        self.api.update(cr, self.adt_uid, '', patient_data)

        patient_id = self.patient_pool.search(
            cr, uid, [('patient_identifier', '=', 'NHSNUM0000')])[0]
        # creates and completes a 'nh.clinical.adt.patient.update' activity
        activity_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.adt.patient.update'],
            ['patient_id', '=', patient_id]
        ])
        self.assertTrue(activity_id, msg="Update Activity not generated")
        activity = self.activity_pool.browse(cr, uid, activity_id[0])
        self.assertEqual(activity.state, 'completed')

    def test_api_update_registers_patient_if_patient_does_not_exist(self):
        cr, uid = self.cr, self.uid
        patient_data = {
            'patient_identifier': 'TESTNHS003',
            'family_name': "Fname30",
            'given_name': 'Gname30',
            'dob': '1988-08-14 18:00:00',
            'gender': 'M',
            'sex': 'M'
        }

        self.api.update(cr, self.adt_uid, 'TESTP0003', patient_data)

        patient_id = self.patient_pool.search(
            cr, uid, [('other_identifier', '=', 'TESTP0003')])
        self.assertTrue(patient_id, msg="Patient was not created")
        # creates and completes a 'nh.clinical.adt.patient.update' activity
        activity_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.adt.patient.update'],
            ['patient_id', '=', patient_id[0]]
        ])
        self.assertTrue(activity_id, msg="Update Activity not generated")
        activity = self.activity_pool.browse(cr, uid, activity_id[0])
        self.assertEqual(activity.state, 'completed')

    def test_adt_patient_update_using_hospital_number_updates_patient(self):
        cr, uid = self.cr, self.uid
        update_data = {
            'family_name': 'Fupdate',
            'given_name': 'Gupdate',
            'other_identifier': 'HOSNUM0000',
            'middle_names': 'Mupdate',
            'patient_identifier': 'NHSNUM0000',
            'dob': '2000-10-01 00:00:00',
            'gender': 'F',
            'sex': 'F'
        }
        update_activity_id = self.update_pool.create_activity(
            cr, self.adt_uid, {}, {})
        self.activity_pool.submit(cr, self.adt_uid, update_activity_id,
                                  update_data)
        self.assertTrue(self.activity_pool.complete(cr, self.adt_uid,
                                                    update_activity_id))
        patient_id = self.patient_pool.search(
            cr, uid, [['other_identifier', '=', 'HOSNUM0000']])[0]
        patient_data = self.patient_pool.read(
            cr, uid, patient_id, ['family_name', 'given_name',
                                  'other_identifier', 'dob', 'gender', 'sex'])
        self.assertEqual(update_data['family_name'],
                         patient_data['family_name'],
                         msg="Patient Update: wrong patient data")
        self.assertEqual(update_data['given_name'], patient_data['given_name'],
                         msg="Patient Update: wrong patient data")
        self.assertEqual(update_data['other_identifier'],
                         patient_data['other_identifier'],
                         msg="Patient Update: wrong patient data")
        self.assertEqual(update_data['dob'], patient_data['dob'],
                         msg="Patient Update: wrong patient data")
        self.assertEqual(update_data['gender'], patient_data['gender'],
                         msg="Patient Update: wrong patient data")
        self.assertEqual(update_data['sex'], patient_data['sex'],
                         msg="Patient Update: wrong patient data")

    def test_adt_patient_update_using_NHS_number_updates_patient(self):
        cr = self.cr
        update_data = {
            'family_name': 'Fupdate',
            'given_name': 'Gupdate',
            'other_identifier': 'HOSNUM0001',
            'patient_identifier': 'NHSNUM0001',
            'dob': '2000-10-01 00:00:00',
            'gender': 'F',
            'sex': 'F'
        }
        update_activity_id = self.update_pool.create_activity(
            cr, self.adt_uid, {}, {})
        self.activity_pool.submit(cr, self.adt_uid, update_activity_id,
                                  update_data)
        self.assertTrue(self.activity_pool.complete(
            cr, self.adt_uid, update_activity_id))

    def test_adt_patient_update_create_activity_no_patient_found_except(self):
        cr = self.cr
        update_data = {
            'family_name': 'Fupdate',
            'given_name': 'Gupdate',
            'other_identifier': 'TESTERROR',
            'dob': '2000-10-01 00:00:00',
            'gender': 'F',
            'sex': 'F'
        }

        with self.assertRaises(except_orm):
            self.update_pool.create_activity(cr, self.adt_uid, {}, update_data)

    def test_adt_patient_update_submit_raises_except_if_no_patient_found(self):
        cr = self.cr
        update_data = {
            'family_name': 'Fupdate',
            'given_name': 'Gupdate',
            'other_identifier': 'TESTERROR',
            'dob': '2000-10-01 00:00:00',
            'gender': 'F',
            'sex': 'F'
        }

        update_activity_id = self.update_pool.create_activity(
            cr, self.adt_uid, {}, {})
        with self.assertRaises(except_orm):
            self.activity_pool.submit(cr, self.adt_uid, update_activity_id,
                                      update_data)
