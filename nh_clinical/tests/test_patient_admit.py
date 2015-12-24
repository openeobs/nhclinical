# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-

import logging

from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


_logger = logging.getLogger(__name__)


class TestPatientAdmit(TransactionCase):

    def setUp(self):
        super(TestPatientAdmit, self).setUp()

        self.api = self.registry('nh.clinical.api')
        self.activity_pool = self.registry('nh.activity')
        self.patient_pool = self.registry('nh.clinical.patient')
        self.admit_pool = self.registry('nh.clinical.adt.patient.admit')
        self.location_pool = self.registry('nh.clinical.location')
        self.users_pool = self.registry('res.users')

        self.ward_A_id = self.location_pool.search(self.cr, self.uid,
                                                   [('code', '=', 'A')])[0]
        self.pos_id = self.location_pool.read(self.cr, self.uid,
                                              self.ward_A_id,
                                              ['pos_id'])['pos_id'][0]
        self.adt_uid = self.users_pool.search(self.cr, self.uid,
                                              [('login', '=', 'adt')])[0]

    def test_adt_patient_admit(self):
        cr, uid = self.cr, self.uid

        doctors = """[{
            'type': 'c',
            'code': 'CON01',
            'title': 'Dr.',
            'given_name': 'Consulting',
            'family_name': 'Doctor',
            'gender': 'F'
        }, {
            'type': 'r',
            'code': 'REF01',
            'title': 'dr.',
            'given_name': 'Referring',
            'family_name': 'Doctor',
            'gender': 'M'
        }]"""

        # Admission data refers to a patient not yet admitted in the system
        # (i.e. a patient without an open spell)
        admit_data = {
            'other_identifier': 'HOSNUM0001',
            'start_date': '2015-04-30 17:00:00',
            'doctors': doctors,
            'code': 'TEST_ADMISSION',
            'location': 'A'
        }

        patient_id = self.patient_pool.search(
            cr, uid, [['other_identifier', '=', 'HOSNUM0001']])[0]
        activity_id = self.admit_pool.create_activity(cr, self.adt_uid, {},
                                                      admit_data)
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(patient_id, activity.data_ref.patient_id.id,
                         msg="Wrong patient id")
        self.assertEqual(self.ward_A_id, activity.data_ref.location_id.id,
                         msg="Wrong location id")
        self.assertEqual(self.pos_id, activity.data_ref.pos_id.id,
                         msg="Wrong POS id")

        # Complete the activity
        self.activity_pool.complete(cr, uid, activity_id)

        admission_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.patient.admission'],
            ['state', '=', 'completed'], ['creator_id', '=', activity_id]])
        self.assertTrue(admission_id, msg="Admission not found!")

        admission = self.activity_pool.browse(cr, uid, admission_id[0])
        self.assertEqual(admission.data_ref.con_doctor_ids[0].code,
                         'CON01', msg="Wrong doctor data")
        self.assertEqual(admission.data_ref.ref_doctor_ids[0].code,
                         'REF01', msg="Wrong doctor data")

        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.parent_id.data_model, 'nh.clinical.spell')
        self.assertEqual(activity.parent_id.patient_id.id, patient_id)

    def test_adt_patient_admit_as_user_with_no_POS_related(self):
        admit_data = {
            'other_identifier': 'HOSNUM0001',
            'location': 'A'
        }
        with self.assertRaises(except_orm):
            self.admit_pool.create_activity(self.cr, self.uid, {}, admit_data)

    def test_adt_admit_patient_with_no_location_data(self):
        admit_data = {
            'other_identifier': 'HOSNUM0001'
        }
        with self.assertRaises(except_orm):
            self.admit_pool.create_activity(self.cr, self.adt_uid, {},
                                            admit_data)

    def test_adt_admit_patient_with_no_identifiers(self):
        admit_data = {
            'location': 'A'
        }
        with self.assertRaises(except_orm):
            self.admit_pool.create_activity(self.cr, self.adt_uid, {},
                                            admit_data)

    def test_adt_patient_admit_using_NHS_number_as_identifier(self):
        cr, uid = self.cr, self.uid
        doctors = """[{
            'type': 'c',
            'code': 'CON01',
            'title': 'Dr.',
            'given_name': 'Consulting',
            'family_name': 'Doctor',
            'gender': 'F'
        }, {
            'type': 'r',
            'code': 'REF01',
            'title': 'dr.',
            'given_name': 'Referring',
            'family_name': 'Doctor',
            'gender': 'M'
        }]"""

        admit_data = {
            'patient_identifier': 'NHSNUM0001',
            'start_date': '2015-04-30 17:00:00',
            'doctors': doctors,
            'code': 'TEST_ADMISSION_WITH_NHS_NUMBER',
            'location': 'A'
        }

        patient_id = self.patient_pool.search(
            cr, uid, [['patient_identifier', '=', 'NHSNUM0001']])[0]
        activity_id = self.admit_pool.create_activity(cr, self.adt_uid, {},
                                                      admit_data)
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(patient_id,
                         activity.data_ref.patient_id.id,
                         msg="Wrong patient id")

        # Complete the activity
        self.activity_pool.complete(cr, uid, activity_id)

        admission_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.patient.admission'],
            ['state', '=', 'completed'], ['creator_id', '=', activity_id]])
        self.assertTrue(admission_id, msg="Admission not found!")

        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.parent_id.data_model, 'nh.clinical.spell')
        self.assertEqual(activity.parent_id.patient_id.id, patient_id)

    def test_api_admit_patient_using_hospital_number(self):
        cr, uid = self.cr, self.uid

        admit_data = {'location': 'A'}

        self.api.admit(cr, self.adt_uid, 'HOSNUM0001', admit_data)

        patient_id = self.patient_pool.search(
            cr, uid, [('other_identifier', '=', 'HOSNUM0001')])[0]
        activity_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.adt.patient.admit'],
            ['patient_id', '=', patient_id]])
        self.assertTrue(activity_id, msg="Admit Activity not generated")
        activity = self.activity_pool.browse(cr, uid, activity_id[0])
        self.assertEqual(activity.state, 'completed')

    def test_api_admit_patient_using_NHS_number(self):
        cr, uid = self.cr, self.uid

        admit_data = {'location': 'A', 'patient_identifier': 'NHSNUM0001'}

        self.api.admit(cr, self.adt_uid, '', admit_data)

        patient_id = self.patient_pool.search(
            cr, uid, [('patient_identifier', '=', 'NHSNUM0001')])[0]
        activity_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.adt.patient.admit'],
            ['patient_id', '=', patient_id]])
        self.assertTrue(activity_id, msg="Admit Activity not generated")
        activity = self.activity_pool.browse(cr, uid, activity_id[0])
        self.assertEqual(activity.state, 'completed')

    def test_api_admit_patient_that_does_not_exist(self):
        """
        Test admitting a patient that does not exist at all in the system.

        The system should automatically create a record for the patient,
        and then admit him without raising any error.
        """
        cr, uid = self.cr, self.uid

        admit_data = {
            'location': 'A',
            'patient_identifier': 'NHS_NUM_999',
            'family_name': 'Fname400',
            'given_name': 'Gname400',
            'dob': '1948-04-29 07:00:00',
            'gender': 'F',
            'sex': 'F'
            }

        self.api.admit(cr, self.adt_uid, 'HOS_NUM_999', admit_data)

        patient_id = self.patient_pool.search(
            cr, uid, [('other_identifier', '=', 'HOS_NUM_999')])
        self.assertTrue(patient_id, msg="Patient was not created")
        activity_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.adt.patient.admit'],
            ['patient_id', '=', patient_id[0]]])
        self.assertTrue(activity_id, msg="Admit Activity not generated")
        activity = self.activity_pool.browse(cr, uid, activity_id[0])
        self.assertEqual(activity.state, 'completed')
