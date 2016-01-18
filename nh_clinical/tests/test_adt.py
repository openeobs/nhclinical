# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import logging

from openerp.tests import common
from openerp.osv.orm import except_orm

_logger = logging.getLogger(__name__)


class testADT(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(testADT, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.users_pool = cls.registry('res.users')
        cls.groups_pool = cls.registry('res.groups')
        cls.partner_pool = cls.registry('res.partner')
        cls.activity_pool = cls.registry('nh.activity')
        cls.patient_pool = cls.registry('nh.clinical.patient')
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.admission_pool = cls.registry('nh.clinical.patient.admission')
        cls.spell_pool = cls.registry('nh.clinical.spell')
        # ADT DATA MODELS
        cls.register_pool = cls.registry('nh.clinical.adt.patient.register')
        cls.admit_pool = cls.registry('nh.clinical.adt.patient.admit')
        cls.cancel_admit_pool = cls.registry(
            'nh.clinical.adt.patient.cancel_admit')
        cls.transfer_pool = cls.registry('nh.clinical.adt.patient.transfer')
        cls.cancel_transfer_pool = cls.registry(
            'nh.clinical.adt.patient.cancel_transfer')
        cls.discharge_pool = cls.registry('nh.clinical.adt.patient.discharge')
        cls.cancel_discharge_pool = cls.registry(
            'nh.clinical.adt.patient.cancel_discharge')
        cls.merge_pool = cls.registry('nh.clinical.adt.patient.merge')
        cls.update_pool = cls.registry('nh.clinical.adt.patient.update')
        cls.spell_update_pool = cls.registry('nh.clinical.adt.spell.update')

        cls.apidemo = cls.registry('nh.clinical.api.demo')

        cls.patient_ids = cls.apidemo.build_unit_test_env1(cr, uid)

        cls.wu_id = cls.location_pool.search(cr, uid, [('code', '=', 'U')])[0]
        cls.wt_id = cls.location_pool.search(cr, uid, [('code', '=', 'T')])[0]
        cls.pos_id = cls.location_pool.read(
            cr, uid, cls.wu_id, ['pos_id'])['pos_id'][0]
        cls.pos_location_id = cls.pos_pool.read(
            cr, uid, cls.pos_id, ['location_id'])['location_id'][0]

        cls.wmu_id = cls.users_pool.search(cr, uid, [('login', '=', 'WMU')])[0]
        cls.wmt_id = cls.users_pool.search(cr, uid, [('login', '=', 'WMT')])[0]
        cls.nu_id = cls.users_pool.search(cr, uid, [('login', '=', 'NU')])[0]
        cls.nt_id = cls.users_pool.search(cr, uid, [('login', '=', 'NT')])[0]
        cls.adt_id = cls.users_pool.search(
            cr, uid, [('groups_id.name', 'in', ['NH Clinical ADT Group']),
                      ('pos_id', '=', cls.pos_id)])[0]

    def test_01_adt_patient_register(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Register a new patient with Hospital Number
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
            cr, self.adt_id, {}, {})
        self.activity_pool.submit(cr, self.adt_id, register_activity_id,
                                  register_data)
        patient_id = self.activity_pool.complete(cr, self.adt_id,
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
        self.assertEqual(register_data['dob'], patient_data['dob'],
                         msg="Patient Register: wrong patient data registered")
        self.assertEqual(register_data['gender'], patient_data['gender'],
                         msg="Patient Register: wrong patient data registered")
        self.assertEqual(register_data['sex'], patient_data['sex'],
                         msg="Patient Register: wrong patient data registered")

        # Scenario 2: Register a new patient with NHS Number
        register_data = {
            'family_name': 'Family',
            'given_name': 'Given',
            'patient_identifier': 'TEST001',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }
        register_activity_id = self.register_pool.create_activity(
            cr, self.adt_id, {}, {})
        self.activity_pool.submit(cr, self.adt_id, register_activity_id,
                                  register_data)
        patient_id = self.activity_pool.complete(cr, self.adt_id,
                                                 register_activity_id)
        self.assertTrue(patient_id,
                        msg="Patient Register: patient id not returned")

        # Scenario 3: Try to Register a patient with incorrect data.
        # Create failure.
        register_data = {
            'family_name': 'Family',
            'given_name': 'Given',
            'other_identifier': 'TEST001',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }

        with self.assertRaises(except_orm):
            self.register_pool.create_activity(cr, self.adt_id, {},
                                               register_data)

        # Scenario 4: Try to Register a patient with incorrect data.
        # Submit failure.
        register_data = {
            'family_name': 'Family',
            'given_name': 'Given',
            'other_identifier': 'TEST001',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }

        register_activity_id = self.register_pool.create_activity(
            cr, self.adt_id, {}, {})
        with self.assertRaises(except_orm):
            self.activity_pool.submit(cr, self.adt_id, register_activity_id,
                                      register_data)

        register_data = {
            'family_name': 'FamilyX',
            'given_name': 'GivenX',
            'other_identifier': 'TEST00X',
            'dob': '1984-10-01 00:00:00',
            'gender': 'F',
            'sex': 'F'
        }
        register_activity_id = self.register_pool.create_activity(
            cr, self.adt_id, {}, {})
        self.activity_pool.submit(cr, self.adt_id, register_activity_id,
                                  register_data)
        self.activity_pool.complete(cr, self.adt_id, register_activity_id)

        register_data = {
            'family_name': 'FamilyY',
            'given_name': 'GivenY',
            'other_identifier': 'TEST00Y',
            'patient_identifier': 'TESTNHSY',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }
        register_activity_id = self.register_pool.create_activity(
            cr, self.adt_id, {}, {})
        self.activity_pool.submit(cr, self.adt_id, register_activity_id,
                                  register_data)
        self.activity_pool.complete(cr, self.adt_id, register_activity_id)

        register_data = {
            'family_name': 'FamilyZ',
            'given_name': 'GivenZ',
            'other_identifier': 'TEST00Z',
            'patient_identifier': 'TESTNHSZ',
            'dob': '1984-10-01 00:00:00',
            'gender': 'F',
            'sex': 'F'
        }
        register_activity_id = self.register_pool.create_activity(
            cr, self.adt_id, {}, {})
        self.activity_pool.submit(cr, self.adt_id, register_activity_id,
                                  register_data)
        self.activity_pool.complete(cr, self.adt_id, register_activity_id)

    def test_02_adt_patient_update(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Update a patient using Hospital Number
        update_data = {
            'family_name': 'Fupdate',
            'given_name': 'Gupdate',
            'other_identifier': 'TEST001',
            'middle_names': 'Mupdate',
            'patient_identifier': 'TESTNHS1',
            'dob': '2000-10-01 00:00:00',
            'gender': 'F',
            'sex': 'F'
        }
        update_activity_id = self.update_pool.create_activity(
            cr, self.adt_id, {}, {})
        self.activity_pool.submit(cr, self.adt_id, update_activity_id,
                                  update_data)
        self.assertTrue(self.activity_pool.complete(cr, self.adt_id,
                                                    update_activity_id))
        patient_id = self.patient_pool.search(
            cr, uid, [['other_identifier', '=', 'TEST001']])[0]
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

        # Scenario 2: Update a patient using NHS Number
        update_data = {
            'family_name': 'Fupdate',
            'given_name': 'Gupdate',
            'other_identifier': 'TEST002',
            'patient_identifier': 'TEST001',
            'dob': '2000-10-01 00:00:00',
            'gender': 'F',
            'sex': 'F'
        }
        update_activity_id = self.update_pool.create_activity(
            cr, self.adt_id, {}, {})
        self.activity_pool.submit(cr, self.adt_id, update_activity_id,
                                  update_data)
        self.assertTrue(self.activity_pool.complete(cr, self.adt_id,
                                                    update_activity_id))

        # Scenario 3: Try to Update a patient with incorrect data.
        # Create failure.
        update_data = {
            'family_name': 'Fupdate',
            'given_name': 'Gupdate',
            'other_identifier': 'TESTERROR',
            'dob': '2000-10-01 00:00:00',
            'gender': 'F',
            'sex': 'F'
        }

        with self.assertRaises(except_orm):
            self.update_pool.create_activity(cr, self.adt_id, {}, update_data)

        # Scenario 4: Try to Update a patient with incorrect data.
        # Submit failure.
        update_activity_id = self.update_pool.create_activity(
            cr, self.adt_id, {}, {})
        with self.assertRaises(except_orm):
            self.activity_pool.submit(cr, self.adt_id, update_activity_id,
                                      update_data)

    def test_03_adt_patient_admit(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Admit a Patient
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
            'other_identifier': 'TEST001',
            'start_date': '2015-04-30 17:00:00',
            'doctors': doctors,
            'code': 'TESTADMISSION01',
            'location': 'U'
        }
        patient_id = self.patient_pool.search(
            cr, uid, [['other_identifier', '=', 'TEST001']])[0]
        activity_id = self.admit_pool.create_activity(cr, self.adt_id, {},
                                                      admit_data)
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(patient_id,
                         activity.data_ref.patient_id.id,
                         msg="Wrong patient id")
        self.assertEqual(self.wu_id, activity.data_ref.location_id.id,
                         msg="Wrong location id")
        self.assertEqual(self.pos_id, activity.data_ref.pos_id.id,
                         msg="Wrong POS id")
        self.activity_pool.complete(cr, uid, activity_id)
        admission_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.patient.admission'],
            ['state', '=', 'completed'], ['creator_id', '=', activity_id]])
        self.assertTrue(admission_id, msg="Admission not found!")
        admission = self.activity_pool.browse(cr, uid, admission_id[0])
        self.assertEqual(admission.data_ref.con_doctor_ids[0].code, 'CON01',
                         msg="Wrong doctor data")
        self.assertEqual(admission.data_ref.ref_doctor_ids[0].code, 'REF01',
                         msg="Wrong doctor data")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.parent_id.data_model, 'nh.clinical.spell')
        self.assertEqual(activity.parent_id.patient_id.id, patient_id)

        # Scenario 2: Admit a Patient with no POS related user
        admit_data = {
            'other_identifier': 'TEST002',
            'location': 'U'
        }
        with self.assertRaises(except_orm):
            self.admit_pool.create_activity(cr, uid, {}, admit_data)

        # Scenario 3: Admit a Patient with no Location
        admit_data = {
            'other_identifier': 'TEST002'
        }
        with self.assertRaises(except_orm):
            self.admit_pool.create_activity(cr, self.adt_id, {}, admit_data)

        # Scenario 4: Admit a Patient with no patient identifiers
        admit_data = {
            'location': 'U'
        }
        with self.assertRaises(except_orm):
            self.admit_pool.create_activity(cr, self.adt_id, {}, admit_data)

        # Scenario 5: Admit a Patient using NHS Number as identifier
        admit_data = {
            'patient_identifier': 'TESTNHSY',
            'start_date': '2015-04-30 17:00:00',
            'doctors': doctors,
            'code': 'TESTADMISSION02',
            'location': 'U'
        }

        patient_id = self.patient_pool.search(
            cr, uid, [['patient_identifier', '=', 'TESTNHSY']])[0]
        activity_id = self.admit_pool.create_activity(cr, self.adt_id, {},
                                                      admit_data)
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(patient_id,
                         activity.data_ref.patient_id.id,
                         msg="Wrong patient id")
        self.activity_pool.complete(cr, uid, activity_id)
        admission_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.patient.admission'],
            ['state', '=', 'completed'], ['creator_id', '=', activity_id]])
        self.assertTrue(admission_id, msg="Admission not found!")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.parent_id.data_model, 'nh.clinical.spell')
        self.assertEqual(activity.parent_id.patient_id.id, patient_id)

    def test_04_adt_patient_cancel_admit(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Cancel an admission with no patient information
        activity_id = self.cancel_admit_pool.create_activity(
            cr, self.adt_id, {}, {})
        with self.assertRaises(except_orm):
            self.activity_pool.submit(cr, uid, activity_id, {})

        # Scenario 2: Cancel an admission with incorrect patient information
        cancel_admit_data = {'other_identifier': 'TESTERROR'}
        with self.assertRaises(except_orm):
            self.cancel_admit_pool.create_activity(cr, self.adt_id, {},
                                                   cancel_admit_data)

        # Scenario 3: Cancel an admission with not admitted patient
        cancel_admit_data = {'other_identifier': 'TEST002'}
        with self.assertRaises(except_orm):
            self.cancel_admit_pool.create_activity(cr, self.adt_id, {},
                                                   cancel_admit_data)

        # Scenario 4: Cancel an admission
        cancel_admit_data = {'other_identifier': 'TEST001'}
        activity_id = self.cancel_admit_pool.create_activity(
            cr, self.adt_id, {}, cancel_admit_data)
        self.activity_pool.complete(cr, self.adt_id, activity_id)
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.data_ref.admission_id.state, 'cancelled')

    def test_05_adt_patient_discharge(self):
        cr, uid = self.cr, self.uid

        admit_data = {
            'other_identifier': 'TEST001',
            'start_date': '2015-04-30 17:00:00',
            'code': 'TESTADMISSION02',
            'location': 'U'
        }
        activity_id = self.admit_pool.create_activity(cr, self.adt_id, {},
                                                      admit_data)
        self.activity_pool.complete(cr, uid, activity_id)

        # Scenario 1: Discharge a Patient
        discharge_data = {
            'other_identifier': 'TEST001',
            'discharge_date': '2015-05-02 18:00:00'
        }
        activity_id = self.discharge_pool.create_activity(cr, self.adt_id, {},
                                                          discharge_data)
        activity = self.activity_pool.browse(cr, uid, activity_id)
        patient_id = self.patient_pool.search(
            cr, uid, [['other_identifier', '=', 'TEST001']])[0]
        self.assertEqual(patient_id,
                         activity.data_ref.patient_id.id,
                         msg="Wrong patient id")
        self.assertEqual(activity.parent_id.data_model, 'nh.clinical.spell')
        self.assertEqual(activity.parent_id.patient_id.id, patient_id)
        self.activity_pool.complete(cr, uid, activity_id)
        discharge_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.patient.discharge'],
            ['state', '=', 'completed'], ['creator_id', '=', activity_id]])
        self.assertTrue(discharge_id, msg="Discharge not found!")

        # Scenario 2: Discharge a Patient with no patient information
        discharge_data = {
            'discharge_date': '2015-05-02 18:00:00'
        }
        with self.assertRaises(except_orm):
            self.discharge_pool.create_activity(cr, self.adt_id, {},
                                                discharge_data)

        # Scenario 3: Discharge a Patient with no POS related user
        discharge_data = {
            'other_identifier': 'TEST002',
            'discharge_date': '2015-05-02 18:00:00'
        }
        with self.assertRaises(except_orm):
            self.discharge_pool.create_activity(cr, uid, {}, discharge_data)

        # Scenario 4: Discharge a Patient using NHS Number
        discharge_data = {
            'patient_identifier': 'TESTNHSY',
            'discharge_date': '2015-05-02 18:00:00'
        }
        activity_id = self.discharge_pool.create_activity(cr, self.adt_id, {},
                                                          discharge_data)
        activity = self.activity_pool.browse(cr, uid, activity_id)
        patient_id = self.patient_pool.search(
            cr, uid, [['patient_identifier', '=', 'TESTNHSY']])[0]
        self.assertEqual(patient_id,
                         activity.data_ref.patient_id.id,
                         msg="Wrong patient id")
        self.activity_pool.complete(cr, uid, activity_id)

        # Scenario 5:
        # Discharge a non admitted Patient without location information.
        discharge_data = {
            'other_identifier': 'TEST00X',
            'discharge_date': '2015-05-02 18:00:00'
        }
        with self.assertRaises(except_orm):
            self.discharge_pool.create_activity(cr, self.adt_id, {},
                                                discharge_data)

        # Scenario 6: Discharge a non admitted Patient
        discharge_data = {
            'other_identifier': 'TEST00X',
            'discharge_date': '2015-05-02 18:00:00',
            'location': 'U'
        }
        activity_id = self.discharge_pool.create_activity(cr, self.adt_id, {},
                                                          discharge_data)
        self.activity_pool.complete(cr, uid, activity_id)

        # Scenario 7: Discharge an already discharged patient
        discharge_data = {
            'other_identifier': 'TEST00X',
            'discharge_date': '2015-05-02 18:00:00',
            'location': 'U'
        }
        with self.assertRaises(except_orm):
            self.discharge_pool.create_activity(cr, self.adt_id, {},
                                                discharge_data)

    def test_06_adt_patient_cancel_discharge(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Cancel Discharge
        cancel_discharge_data = {'other_identifier': 'TEST00Y'}
        activity_id = self.cancel_discharge_pool.create_activity(
            cr, self.adt_id, {}, cancel_discharge_data)
        self.activity_pool.complete(cr, self.adt_id, activity_id)
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.data_ref.discharge_id.state, 'cancelled')

        # Scenario 2: Cancel discharge with no patient information
        activity_id = self.cancel_discharge_pool.create_activity(
            cr, self.adt_id, {}, {})
        with self.assertRaises(except_orm):
            self.activity_pool.submit(cr, uid, activity_id, {})

        # Scenario 3: Cancel discharge with incorrect patient information
        cancel_discharge_data = {'other_identifier': 'TESTERROR'}
        with self.assertRaises(except_orm):
            self.cancel_discharge_pool.create_activity(cr, self.adt_id, {},
                                                       cancel_discharge_data)

        # Scenario 4: Cancel discharge with not discharged patient
        cancel_discharge_data = {'other_identifier': 'TEST002'}
        with self.assertRaises(except_orm):
            self.cancel_discharge_pool.create_activity(cr, self.adt_id, {},
                                                       cancel_discharge_data)

        cancel_discharge_data = {'other_identifier': 'TEST001'}
        activity_id = self.cancel_discharge_pool.create_activity(
            cr, self.adt_id, {}, cancel_discharge_data)
        self.activity_pool.complete(cr, self.adt_id, activity_id)

    def test_07_adt_patient_transfer(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Transfer a Patient
        transfer_data = {
            'other_identifier': 'TEST001',
            'location': 'T'
        }
        activity_id = self.transfer_pool.create_activity(cr, self.adt_id, {},
                                                         transfer_data)
        activity = self.activity_pool.browse(cr, uid, activity_id)
        patient_id = self.patient_pool.search(
            cr, uid, [['other_identifier', '=', 'TEST001']])[0]
        self.assertEqual(patient_id,
                         activity.data_ref.patient_id.id,
                         msg="Wrong patient id")
        self.assertEqual(activity.data_ref.location_id.id, self.wt_id,
                         msg="Wrong location id")
        self.assertEqual(activity.parent_id.data_model, 'nh.clinical.spell')
        self.assertEqual(activity.parent_id.patient_id.id, patient_id)
        self.activity_pool.complete(cr, uid, activity_id)
        transfer_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.patient.transfer'],
            ['state', '=', 'completed'], ['creator_id', '=', activity_id]])
        self.assertTrue(transfer_id, msg="Transfer not found!")

        # Scenario 2: Transfer a Patient using NHS Number
        transfer_data = {
            'patient_identifier': 'TESTNHSY',
            'location': 'T'
        }
        activity_id = self.transfer_pool.create_activity(
            cr, self.adt_id, {}, transfer_data)
        activity = self.activity_pool.browse(cr, uid, activity_id)
        patient_id = self.patient_pool.search(
            cr, uid, [['patient_identifier', '=', 'TESTNHSY']])[0]
        self.assertEqual(patient_id,
                         activity.data_ref.patient_id.id,
                         msg="Wrong patient id")
        self.activity_pool.complete(cr, uid, activity_id)
        transfer_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.patient.transfer'],
            ['state', '=', 'completed'], ['creator_id', '=', activity_id]])
        self.assertTrue(transfer_id, msg="Transfer not found!")

        # Scenario 3.1:
        # Transfer a not admitted Patient not providing origin location.
        transfer_data = {
            'other_identifier': 'TEST00X',
            'location': 'T'
        }
        with self.assertRaises(except_orm):
            self.transfer_pool.create_activity(cr, self.adt_id, {},
                                               transfer_data)

        # Scenario 3.2:
        # Transfer a not admitted Patient providing origin location.
        transfer_data = {
            'other_identifier': 'TEST00X',
            'original_location': 'X',
            'location': 'T'
        }
        activity_id = self.transfer_pool.create_activity(cr, self.adt_id, {},
                                                         transfer_data)
        activity = self.activity_pool.browse(cr, uid, activity_id)
        patient_id = self.patient_pool.search(
            cr, uid, [['other_identifier', '=', 'TEST00X']])[0]
        self.assertEqual(patient_id,
                         activity.data_ref.patient_id.id,
                         msg="Wrong patient id")
        self.assertEqual(activity.data_ref.location_id.id, self.wt_id,
                         msg="Wrong location id")
        self.assertEqual(activity.parent_id.data_model, 'nh.clinical.spell')
        self.assertEqual(activity.parent_id.patient_id.id, patient_id)
        self.activity_pool.complete(cr, uid, activity_id)
        transfer_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.patient.transfer'],
            ['state', '=', 'completed'], ['creator_id', '=', activity_id]])
        self.assertTrue(transfer_id, msg="Transfer not found!")

        # Scenario 4: Transfer a Patient with no patient information
        transfer_data = {
            'location': 'T'
        }
        with self.assertRaises(except_orm):
            self.transfer_pool.create_activity(cr, self.adt_id, {},
                                               transfer_data)

        # Scenario 5: Transfer a Patient with no location information
        transfer_data = {
            'other_identifier': 'TEST001'
        }
        with self.assertRaises(except_orm):
            self.transfer_pool.create_activity(cr, self.adt_id, {},
                                               transfer_data)

        # Scenario 6: Transfer a Patient with no POS related user
        transfer_data = {
            'other_identifier': 'TEST001',
            'location': 'T'
        }
        with self.assertRaises(except_orm):
            self.transfer_pool.create_activity(cr, uid, {}, transfer_data)

    def test_08_adt_patient_cancel_transfer(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Cancel transfer with no patient information
        activity_id = self.cancel_transfer_pool.create_activity(
            cr, self.adt_id, {}, {})
        with self.assertRaises(except_orm):
            self.activity_pool.submit(cr, uid, activity_id, {})

        # Scenario 2: Cancel transfer with incorrect patient information
        cancel_transfer_data = {'other_identifier': 'TESTERROR'}
        with self.assertRaises(except_orm):
            self.cancel_transfer_pool.create_activity(cr, self.adt_id, {},
                                                      cancel_transfer_data)

        # Scenario 3: Cancel transfer with not transferred patient
        cancel_transfer_data = {'other_identifier': 'TEST002'}
        with self.assertRaises(except_orm):
            self.cancel_transfer_pool.create_activity(cr, self.adt_id, {},
                                                      cancel_transfer_data)

        # Scenario 4: Cancel Transfer
        cancel_transfer_data = {'other_identifier': 'TEST001'}
        activity_id = self.cancel_transfer_pool.create_activity(
            cr, self.adt_id, {}, cancel_transfer_data)
        self.activity_pool.complete(cr, self.adt_id, activity_id)
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.data_ref.transfer_id.state, 'cancelled')

    def test_09_adt_patient_spell_update(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Update a Spell
        doctors = """[{
            'type': 'c',
            'code': 'CON02',
            'title': 'Dr.',
            'given_name': 'Consulting',
            'family_name': 'Doctor',
            'gender': 'F'
        }, {
            'type': 'r',
            'code': 'REF02',
            'title': 'dr.',
            'given_name': 'Referring',
            'family_name': 'Doctor',
            'gender': 'M'
        }]"""

        update_data = {
            'other_identifier': 'TEST001',
            'start_date': '2015-05-05 17:00:00',
            'doctors': doctors,
            'code': 'TESTADMISSION03',
            'location': 'T'
        }
        patient_id = self.patient_pool.search(
            cr, uid, [['other_identifier', '=', 'TEST001']])[0]
        activity_id = self.spell_update_pool.create_activity(
            cr, self.adt_id, {}, update_data)
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(patient_id,
                         activity.data_ref.patient_id.id,
                         msg="Wrong patient id")
        self.assertEqual(self.wt_id, activity.data_ref.location_id.id,
                         msg="Wrong location id")
        self.assertEqual(self.pos_id, activity.data_ref.pos_id.id,
                         msg="Wrong POS id")
        self.activity_pool.complete(cr, uid, activity_id)
        spell = self.activity_pool.browse(cr, uid, activity.parent_id.id)
        self.assertEqual(spell.data_ref.con_doctor_ids[0].code, 'CON02',
                         msg="Wrong doctor data")
        self.assertEqual(spell.data_ref.ref_doctor_ids[0].code, 'REF02',
                         msg="Wrong doctor data")
        self.assertEqual(spell.data_ref.start_date, '2015-05-05 17:00:00')
        self.assertEqual(spell.data_ref.code, 'TESTADMISSION03')
        self.assertEqual(spell.data_ref.location_id.id, self.wt_id,
                         msg="Patient was not moved")

        # Scenario 2: Update a Spell with no POS related user
        update_data = {
            'other_identifier': 'TEST001',
            'location': 'U'
        }
        with self.assertRaises(except_orm):
            self.spell_update_pool.create_activity(cr, uid, {}, update_data)

        # Scenario 3: Update a Spell with no Location
        update_data = {
            'other_identifier': 'TEST001'
        }
        with self.assertRaises(except_orm):
            self.spell_update_pool.create_activity(cr, self.adt_id, {},
                                                   update_data)

        # Scenario 4: Update a Spell with no patient identifiers
        update_data = {
            'location': 'U'
        }
        with self.assertRaises(except_orm):
            self.spell_update_pool.create_activity(cr, self.adt_id, {},
                                                   update_data)

        # Scenario 5: Update a Spell with no doctor data
        update_data = {
            'other_identifier': 'TEST001',
            'start_date': '2015-05-05 17:00:00',
            'code': 'TESTADMISSION03',
            'location': 'T'
        }
        activity_id = self.spell_update_pool.create_activity(
            cr, self.adt_id, {}, update_data)
        self.activity_pool.complete(cr, uid, activity_id)
        spell = self.activity_pool.browse(cr, uid, activity.parent_id.id)
        self.assertFalse(spell.data_ref.con_doctor_ids,
                         msg="Wrong doctor data")
        self.assertFalse(spell.data_ref.ref_doctor_ids,
                         msg="Wrong doctor  data")

        # Scenario 6: Update a Spell using NHS Number as identifier
        update_data = {
            'patient_identifier': 'TESTNHSY',
            'start_date': '2015-04-30 17:00:00',
            'doctors': doctors,
            'code': 'TESTADMISSION02',
            'location': 'T'
        }

        patient_id = self.patient_pool.search(
            cr, uid, [['patient_identifier', '=', 'TESTNHSY']])[0]
        activity_id = self.spell_update_pool.create_activity(
            cr, self.adt_id, {}, update_data)
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(patient_id,
                         activity.data_ref.patient_id.id,
                         msg="Wrong patient id")
        self.activity_pool.complete(cr, uid, activity_id)

        # Scenario 6: Update a Spell with not admitted patient
        update_data = {
            'other_identifier': 'TEST00Z',
            'start_date': '2015-04-30 17:00:00',
            'doctors': doctors,
            'code': 'TESTADMISSION0Z',
            'location': 'T'
        }
        with self.assertRaises(except_orm):
            self.spell_update_pool.create_activity(
                cr, self.adt_id, {}, update_data)

    def test_10_adt_patient_merge(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Create merge activity with incorrect patient data
        with self.assertRaises(except_orm):
            self.merge_pool.create_activity(cr, self.adt_id, {},
                                            {'from_identifier': 'TESTERROR'})
        with self.assertRaises(except_orm):
            self.merge_pool.create_activity(cr, self.adt_id, {},
                                            {'into_identifier': 'TESTERROR'})

        # Scenario 2: Try to merge with missing source or destination patients
        activity_id = self.merge_pool.create_activity(
            cr, self.adt_id, {}, {'from_identifier': 'TEST001'})
        with self.assertRaises(except_orm):
            self.activity_pool.complete(cr, self.adt_id, activity_id)
        activity_id = self.merge_pool.create_activity(
            cr, self.adt_id, {}, {'into_identifier': 'TEST00X'})
        with self.assertRaises(except_orm):
            self.activity_pool.complete(cr, self.adt_id, activity_id)

        # Scenario: Merge two patients
        source_patient_id = self.patient_pool.search(
            cr, uid, [['other_identifier', '=', 'TEST001']])
        self.patient_pool.write(cr, uid, source_patient_id,
                                {'current_location_id': self.wu_id})
        merge_data = {
            'from_identifier': 'TEST001',
            'into_identifier': 'TEST00X',
        }
        activity_id = self.merge_pool.create_activity(cr, self.adt_id, {},
                                                      merge_data)
        activity_ids = self.activity_pool.search(
            cr, uid, [('patient_id.other_identifier', '=', 'TEST001')])
        self.assertTrue(len(activity_ids),
                        msg="There are no activities to be given "
                            "to destination patient")
        self.activity_pool.complete(cr, self.adt_id, activity_id)
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertFalse(activity.data_ref.source_patient_id.active,
                         msg="Source patient was not deactivated")
        for a in self.activity_pool.browse(cr, uid, activity_ids):
            self.assertEqual(a.patient_id.other_identifier, 'TEST00X')
        self.assertEqual(activity.data_ref.dest_patient_id.given_name,
                         'GivenX', msg="Destination patient data wrong update")
        self.assertEqual(activity.data_ref.dest_patient_id.middle_names,
                         'Mupdate',
                         msg="Destination patient data wrong update")
