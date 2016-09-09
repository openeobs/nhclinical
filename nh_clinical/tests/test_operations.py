# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
from openerp.tests import common
from openerp.osv.orm import except_orm


class TestOperations(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestOperations, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.users_pool = cls.registry('res.users')
        cls.groups_pool = cls.registry('res.groups')
        cls.partner_pool = cls.registry('res.partner')
        cls.activity_pool = cls.registry('nh.activity')
        cls.patient_pool = cls.registry('nh.clinical.patient')
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.spell_pool = cls.registry('nh.clinical.spell')
        # OPERATIONS DATA MODELS
        cls.placement_pool = cls.registry('nh.clinical.patient.placement')
        cls.move_pool = cls.registry('nh.clinical.patient.move')
        cls.swap_pool = cls.registry('nh.clinical.patient.swap_beds')
        cls.follow_pool = cls.registry('nh.clinical.patient.follow')
        cls.unfollow_pool = cls.registry('nh.clinical.patient.unfollow')
        cls.admission_pool = cls.registry('nh.clinical.patient.admission')
        cls.discharge_pool = cls.registry('nh.clinical.patient.discharge')
        cls.transfer_pool = cls.registry('nh.clinical.patient.transfer')

        cls.wm_group_id = cls.groups_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Shift Coordinator Group']])
        cls.nurse_group_id = cls.groups_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Nurse Group']])
        cls.admin_group_id = cls.groups_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Admin Group']])

        cls.hospital_id = cls.location_pool.create(
            cr, uid, {'name': 'Test Hospital', 'code': 'TESTHOSP',
                      'usage': 'hospital'})
        cls.pos_id = cls.pos_pool.create(
            cr, uid, {'name': 'Test POS', 'location_id': cls.hospital_id})

        cls.adt_uid = cls.users_pool.create(
            cr, uid, {'name': 'Admin 0', 'login': 'user_000',
                      'password': 'user_000',
                      'groups_id': [[4, cls.admin_group_id[0]]],
                      'pos_id': cls.pos_id})

        cls.locations = {}
        cls.users = {}
        for i in range(3):
            wid = cls.location_pool.create(
                cr, uid,
                {'name': 'Ward'+str(i), 'code': 'WARD'+str(i), 'usage': 'ward',
                 'parent_id': cls.hospital_id, 'type': 'poc'})
            cls.locations[wid] = [
                cls.location_pool.create(
                    cr, uid, {'name': 'Bed'+str(i)+str(j),
                              'code': 'BED'+str(i)+str(j),
                              'usage': 'bed', 'parent_id': wid,
                              'type': 'poc'}) for j in range(3)
            ]
            cls.users[wid] = {
                'wm': cls.users_pool.create(
                    cr, uid, {'name': 'WM'+str(i), 'login': 'wm'+str(i),
                              'password': 'wm'+str(i),
                              'groups_id': [[4, cls.wm_group_id[0]]],
                              'pos_id': cls.pos_id,
                              'location_ids': [[6, 0, [wid]]]}),
                'n': cls.users_pool.create(
                    cr, uid, {'name': 'N'+str(i), 'login': 'n'+str(i),
                              'password': 'n'+str(i),
                              'groups_id': [[4, cls.nurse_group_id[0]]],
                              'pos_id': cls.pos_id,
                              'location_ids': [[6, 0, cls.locations[wid]]]})
            }

        cls.patients = [
            cls.patient_pool.create(
                cr, uid,
                {'other_identifier': 'TESTP000'+str(i),
                 'given_name': 'John',
                 'family_name': 'Smith',
                 'middle_names': 'Clarke '+str(i),
                 'patient_identifier': 'TESTNHS0'+str(i)}) for i in range(7)
        ]

    def test_01_admission_submit_complete(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Admit a patient
        admission_data = {
            'pos_id': self.pos_id,
            'patient_id': self.patients[0],
            'location_id': self.locations.keys()[0],
            'code': 'TESTADMISSION01',
            'start_date': '2015-05-10 15:00:00'
        }
        admission_id = self.admission_pool.create_activity(
            cr, self.adt_uid, {}, admission_data)
        self.activity_pool.complete(cr, self.adt_uid, admission_id)
        spell_id = self.activity_pool.search(
            cr, uid, [['data_model', '=', 'nh.clinical.spell'],
                      ['state', '=', 'started'],
                      ['patient_id', '=', self.patients[0]],
                      ['creator_id', '=', admission_id]])
        self.assertTrue(spell_id,
                        msg="Spell not created correctly after Admission")

        # Scenario 2: Admit an already admitted patient
        with self.assertRaises(except_orm):
            self.admission_pool.create_activity(cr, uid, {}, admission_data)

        # Scenario 3: Admission without patient data
        admission_data = {
            'pos_id': self.pos_id,
            'location_id': self.locations.keys()[0],
            'code': 'TESTADMISSION01',
            'start_date': '2015-05-10 15:00:00'
        }
        with self.assertRaises(except_orm):
            self.admission_pool.create_activity(cr, uid, {}, admission_data)

        admission_data = {
            'pos_id': self.pos_id,
            'location_id': self.locations.keys()[1],
            'patient_id': self.patients[2],
            'code': 'TESTADMISSION02',
            'start_date': '2015-05-10 15:00:00'
        }
        admission_id = self.admission_pool.create_activity(
            cr, self.adt_uid, {}, admission_data)
        self.activity_pool.complete(cr, self.adt_uid, admission_id)

        admission_data = {
            'pos_id': self.pos_id,
            'location_id': self.locations.keys()[2],
            'patient_id': self.patients[3],
            'code': 'TESTADMISSION03',
            'start_date': '2015-05-10 15:00:00'
        }
        admission_id = self.admission_pool.create_activity(
            cr, self.adt_uid, {}, admission_data)
        self.activity_pool.complete(cr, self.adt_uid, admission_id)

        admission_data = {
            'pos_id': self.pos_id,
            'location_id': self.locations.keys()[0],
            'patient_id': self.patients[4],
            'code': 'TESTADMISSION04',
            'start_date': '2015-05-10 15:00:00'
        }
        admission_id = self.admission_pool.create_activity(
            cr, self.adt_uid, {}, admission_data)
        self.activity_pool.complete(cr, self.adt_uid, admission_id)

        admission_data = {
            'pos_id': self.pos_id,
            'location_id': self.locations.keys()[0],
            'patient_id': self.patients[6],
            'code': 'TESTADMISSION06',
            'start_date': '2015-05-10 15:00:00'
        }
        admission_id = self.admission_pool.create_activity(
            cr, self.adt_uid, {}, admission_data)
        self.activity_pool.complete(cr, self.adt_uid, admission_id)

    def test_02_get_last_admission(self):
        cr, uid = self.cr, self.uid

        admission_id = self.activity_pool.search(
            cr, uid, [['patient_id', '=', self.patients[0]],
                      ['data_model', '=', 'nh.clinical.patient.admission']])

        # Scenario 1: Admission exists
        self.assertEqual(
            self.admission_pool.get_last(cr, uid, self.patients[0]),
            admission_id[0])

        # Scenario 2: Admission does not exist
        self.assertFalse(
            self.admission_pool.get_last(cr, uid, self.patients[1]))

        # Scenario 3: Exception 'True', Admission exists
        with self.assertRaises(except_orm):
            self.admission_pool.get_last(cr, uid, self.patients[0],
                                         exception='True')

        # Scenario 4: Exception 'False', Admission does not exist
        with self.assertRaises(except_orm):
            self.admission_pool.get_last(cr, uid, self.patients[1],
                                         exception='False')

    def test_03_admission_cancel(self):
        cr, uid = self.cr, self.uid

        admission_id = self.activity_pool.search(
            cr, uid, [['patient_id', '=', self.patients[0]],
                      ['data_model', '=', 'nh.clinical.patient.admission']])
        admission = self.activity_pool.browse(cr, uid, admission_id)

        # Scenario 1: Cancel an admission
        self.activity_pool.cancel(cr, self.adt_uid, admission_id[0])
        activity_ids = self.activity_pool.search(cr, uid, [
            ['id', 'child_of', admission.parent_id.id],
            ['state', 'not in', ['completed', 'cancelled']]])
        self.assertFalse(activity_ids, msg="Spell activities not cancelled")

        # prepare for future tests
        admission_data = {
            'pos_id': self.pos_id,
            'patient_id': self.patients[0],
            'location_id': self.locations.keys()[0],
            'code': 'TESTADMISSION11',
            'start_date': '2015-05-10 15:00:00'
        }
        admission_id = self.admission_pool.create_activity(
            cr, self.adt_uid, {}, admission_data)
        self.activity_pool.complete(cr, self.adt_uid, admission_id)

    def test_04_placement_submit_complete(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Place a patient into a bed
        ward_id = self.locations.keys()[2]
        bed_id = self.locations[ward_id][0]
        wm_id = self.users[ward_id]['wm']
        placement_data = {
            'suggested_location_id': ward_id,
            'patient_id': self.patients[3]
        }
        placement_id = self.placement_pool.create_activity(
            cr, self.adt_uid, {}, placement_data)
        self.activity_pool.submit(cr, wm_id, placement_id,
                                  {'location_id': bed_id})
        self.activity_pool.complete(cr, wm_id, placement_id)
        move_ids = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.patient.move'],
            ['state', '=', 'completed'],
            ['patient_id', '=', self.patients[3]],
            ['creator_id', '=', placement_id]])
        self.assertTrue(move_ids,
                        msg="Movement Activity not completed after placement")
        spell_id = self.activity_pool.search(
            cr, uid, [['data_model', '=', 'nh.clinical.spell'],
                      ['state', '=', 'started'],
                      ['patient_id', '=', self.patients[3]]])
        spell = self.activity_pool.browse(cr, uid, spell_id[0])
        self.assertEqual(spell.data_ref.location_id.id, bed_id,
                         msg="Placement did not update spell location")
        patient = self.patient_pool.browse(cr, uid, self.patients[3])
        self.assertEqual(
            patient.current_location_id.id, bed_id,
            msg="Placement did not update current patient location")

        # Scenario 2: Try to place a patient into a ward
        placement_data = {
            'suggested_location_id': ward_id,
            'patient_id': self.patients[4]
        }
        placement_id = self.placement_pool.create_activity(
            cr, self.adt_uid, {}, placement_data)
        with self.assertRaises(except_orm):
            self.activity_pool.submit(cr, wm_id, placement_id,
                                      {'location_id': ward_id})

        # Scenario 3: Try to place a patient without destination location
        placement_data = {
            'suggested_location_id': ward_id,
            'patient_id': self.patients[4]
        }
        placement_id = self.placement_pool.create_activity(
            cr, self.adt_uid, {}, placement_data)
        with self.assertRaises(except_orm):
            self.activity_pool.complete(cr, wm_id, placement_id)

        # Scenario 4: Try to place a non admitted patient
        bed_id = self.locations[ward_id][1]
        placement_data = {
            'suggested_location_id': ward_id,
            'patient_id': self.patients[5]
        }
        placement_id = self.placement_pool.create_activity(
            cr, self.adt_uid, {}, placement_data)
        self.activity_pool.submit(cr, wm_id, placement_id,
                                  {'location_id': bed_id})
        with self.assertRaises(except_orm):
            self.activity_pool.complete(cr, wm_id, placement_id)

    def test_05_placement_form_description(self):
        cr = self.cr

        ward_id = self.locations.keys()[2]
        wm_id = self.users[ward_id]['wm']
        bed_id = self.locations[ward_id][1]

        # Scenario 1: Get form description for a patient with no placement
        fd = self.placement_pool.get_form_description(cr, wm_id,
                                                      self.patients[0])
        for field in fd:
            if field['name'] == 'location_id':
                self.assertFalse(field['selection'],
                                 msg="Location selection incorrect")

        # Scenario 2: Get form description for a patient with placement
        placement_data = {
            'suggested_location_id': ward_id,
            'patient_id': self.patients[4]
        }
        placement_id = self.placement_pool.create_activity(
            cr, self.adt_uid, {}, placement_data)
        fd = self.placement_pool.get_form_description(cr, wm_id,
                                                      self.patients[4])
        for field in fd:
            if field['name'] == 'location_id':
                self.assertTrue(field['selection'],
                                msg="Location selection incorrect")
        self.activity_pool.submit(cr, wm_id, placement_id,
                                  {'location_id': bed_id})
        self.activity_pool.complete(cr, wm_id, placement_id)

        ward_id = self.locations.keys()[0]
        wm_id = self.users[ward_id]['wm']
        bed_id = self.locations[ward_id][0]
        placement_data = {
            'suggested_location_id': ward_id,
            'patient_id': self.patients[6]
        }
        placement_id = self.placement_pool.create_activity(
            cr, self.adt_uid, {}, placement_data)
        self.activity_pool.submit(cr, wm_id, placement_id,
                                  {'location_id': bed_id})
        self.activity_pool.complete(cr, wm_id, placement_id)

    def test_06_swap_beds(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Swap patients between two beds
        ward1_id = self.locations.keys()[2]
        wm_id = self.users[ward1_id]['wm']
        ward2_id = self.locations.keys()[0]
        swap_data = {
            'location1_id': self.locations[ward1_id][0],  # self.patients[3]
            'location2_id': self.locations[ward1_id][1]  # self.patients[4]
        }
        swap_id = self.swap_pool.create_activity(cr, wm_id, {}, swap_data)
        self.activity_pool.complete(cr, wm_id, swap_id)
        move_ids = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.patient.move'],
            ['state', '=', 'completed'], ['patient_id', '=', self.patients[3]],
            ['creator_id', '=', swap_id]])
        self.assertTrue(move_ids,
                        msg="Movement Activity not completed after swap")
        move_ids = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.patient.move'],
            ['state', '=', 'completed'], ['patient_id', '=', self.patients[4]],
            ['creator_id', '=', swap_id]])
        self.assertTrue(move_ids,
                        msg="Movement Activity not completed after swap")
        spell_id = self.activity_pool.search(
            cr, uid, [['data_model', '=', 'nh.clinical.spell'],
                      ['state', '=', 'started'],
                      ['patient_id', '=', self.patients[3]]])
        spell = self.activity_pool.browse(cr, uid, spell_id[0])
        self.assertEqual(spell.data_ref.location_id.id,
                         self.locations[ward1_id][1],
                         msg="Swap did not update spell location")
        patient = self.patient_pool.browse(cr, uid, self.patients[3])
        self.assertEqual(patient.current_location_id.id,
                         self.locations[ward1_id][1],
                         msg="Swap did not update current patient location")
        spell_id = self.activity_pool.search(
            cr, uid, [['data_model', '=', 'nh.clinical.spell'],
                      ['state', '=', 'started'],
                      ['patient_id', '=', self.patients[4]]])
        spell = self.activity_pool.browse(cr, uid, spell_id[0])
        self.assertEqual(spell.data_ref.location_id.id,
                         self.locations[ward1_id][0],
                         msg="Swap did not update spell location")
        patient = self.patient_pool.browse(cr, uid, self.patients[4])
        self.assertEqual(patient.current_location_id.id,
                         self.locations[ward1_id][0],
                         msg="Swap did not update current patient location")

        # Scenario 2: Try to swap patients using an empty location
        swap_data = {
            'location1_id': self.locations[ward1_id][0],  # self.patients[4]
            'location2_id': self.locations[ward1_id][2]  # no patient
        }
        with self.assertRaises(except_orm):
            self.swap_pool.create_activity(cr, wm_id, {}, swap_data)

        swap_data = {
            'location1_id': self.locations[ward1_id][2],  # no patient
            'location2_id': self.locations[ward1_id][1]  # self.patients[3]
        }
        with self.assertRaises(except_orm):
            self.swap_pool.create_activity(cr, wm_id, {}, swap_data)

        # Scenario 3: Try to swap patients from different wards
        swap_data = {
            'location1_id': self.locations[ward1_id][0],  # self.patients[4]
            'location2_id': self.locations[ward2_id][0]  # self.patients[6]
        }
        with self.assertRaises(except_orm):
            self.swap_pool.create_activity(cr, wm_id, {}, swap_data)

    def test_07_discharge_submit_complete(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Discharge a patient
        discharge_data = {
            'patient_id': self.patients[2],
            'discharge_date': '2015-05-14 16:00:00'
        }
        discharge_id = self.discharge_pool.create_activity(
            cr, self.adt_uid, {}, discharge_data)
        self.activity_pool.complete(cr, self.adt_uid, discharge_id)
        discharge = self.activity_pool.browse(cr, uid, discharge_id)
        self.assertEqual(discharge.parent_id.data_model, 'nh.clinical.spell')
        self.assertEqual(discharge.parent_id.state, 'completed')
        self.assertEqual(discharge.parent_id.date_terminated,
                         '2015-05-14 16:00:00')
        self.assertEqual(discharge.data_ref.location_id.id,
                         self.locations.keys()[1],
                         msg="Discharged from 'location' not updated")
        self.assertNotEqual(discharge.parent_id.location_id.id,
                            discharge.data_ref.location_id.id)

        # Scenario 2: Discharge a patient without discharge date
        discharge_data = {
            'patient_id': self.patients[3]
        }
        discharge_id = self.discharge_pool.create_activity(
            cr, self.adt_uid, {}, discharge_data)
        self.assertTrue(self.activity_pool.complete(cr, self.adt_uid,
                                                    discharge_id))

        # Scenario 3: Discharge a discharged patient
        with self.assertRaises(except_orm):
            self.discharge_pool.create_activity(
                cr, self.adt_uid, {}, discharge_data)

        # Scenario 4: Admission without patient data
        discharge_data = {
            'discharge_date': '2015-05-14 16:00:00'
        }
        with self.assertRaises(except_orm):
            self.discharge_pool.create_activity(
                cr, self.adt_uid, {}, discharge_data)

    def test_08_move_submit_complete(self):
        cr, uid = self.cr, self.uid

        ward_id = self.locations.keys()[2]
        wm_id = self.users[ward_id]['wm']
        bed_id = self.locations[ward_id][1]

        # Scenario 1: Move a patient
        move_data = {
            'location_id': bed_id,
            'patient_id': self.patients[4]
        }
        move_id = self.move_pool.create_activity(cr, wm_id, {}, move_data)
        self.activity_pool.complete(cr, wm_id, move_id)
        spell_id = self.activity_pool.search(
            cr, uid, [['data_model', '=', 'nh.clinical.spell'],
                      ['state', '=', 'started'],
                      ['patient_id', '=', self.patients[4]]])
        spell = self.activity_pool.browse(cr, uid, spell_id[0])
        self.assertEqual(spell.data_ref.location_id.id,
                         self.locations[ward_id][1],
                         msg="Move did not update spell location")
        patient = self.patient_pool.browse(cr, uid, self.patients[4])
        self.assertEqual(patient.current_location_id.id,
                         self.locations[ward_id][1],
                         msg="Move did not update current patient location")

        # Scenario 2: Move a non admitted patient
        move_data = {
            'location_id': ward_id,
            'patient_id': self.patients[5]
        }
        move_id = self.move_pool.create_activity(cr, wm_id, {}, move_data)
        self.assertTrue(self.activity_pool.complete(cr, wm_id, move_id))

        # Scenario 3: Try to move a patient with no location information
        move_data = {
            'patient_id': self.patients[5]
        }
        move_id = self.move_pool.create_activity(cr, wm_id, {}, move_data)
        with self.assertRaises(except_orm):
            self.activity_pool.complete(cr, wm_id, move_id)

        # prepare for cancel discharge scenario
        discharge_data = {
            'patient_id': self.patients[4]
        }
        discharge_id = self.discharge_pool.create_activity(
            cr, self.adt_uid, {}, discharge_data)
        self.assertTrue(self.activity_pool.complete(cr, self.adt_uid,
                                                    discharge_id))

    def test_09_get_last_discharge(self):
        cr, uid = self.cr, self.uid

        discharge_id = self.activity_pool.search(
            cr, uid, [['patient_id', '=', self.patients[2]],
                      ['data_model', '=', 'nh.clinical.patient.discharge']])

        # Scenario 1: Discharge exists
        self.assertTrue(discharge_id, msg="No discharge found!")
        self.assertEqual(
            self.discharge_pool.get_last(cr, uid, self.patients[2]),
            discharge_id[0])

        # Scenario 2: Discharge does not exist
        self.assertFalse(self.discharge_pool.get_last(cr, uid,
                                                      self.patients[0]))

        # Scenario 3: Exception 'True', Discharge exists
        with self.assertRaises(except_orm):
            self.discharge_pool.get_last(cr, uid, self.patients[2],
                                         exception='True')

        # Scenario 4: Exception 'False', Discharge does not exist
        with self.assertRaises(except_orm):
            self.discharge_pool.get_last(cr, uid, self.patients[0],
                                         exception='False')

    def test_10_patient_discharge_cancel(self):
        cr, uid = self.cr, self.uid

        discharge_id = self.activity_pool.search(
            cr, uid, [['patient_id', '=', self.patients[2]],
                      ['data_model', '=', 'nh.clinical.patient.discharge']])

        # Scenario 1: Cancel a discharge with source location Ward
        self.activity_pool.cancel(cr, self.adt_uid, discharge_id[0])
        discharge = self.activity_pool.browse(cr, uid, discharge_id[0])
        self.assertEqual(discharge.parent_id.state, 'started')
        self.assertFalse(discharge.parent_id.date_terminated)
        self.assertEqual(discharge.parent_id.location_id.id,
                         discharge.data_ref.location_id.id)

        # Scenario 2: Cancel a discharge with source location Available Bed
        discharge_id = self.activity_pool.search(
            cr, uid, [['patient_id', '=', self.patients[3]],
                      ['data_model', '=', 'nh.clinical.patient.discharge']])
        self.activity_pool.cancel(cr, self.adt_uid, discharge_id[0])
        discharge = self.activity_pool.browse(cr, uid, discharge_id[0])
        self.assertEqual(discharge.parent_id.location_id.id,
                         discharge.data_ref.location_id.id)

        # Scenario 3: Cancel a discharge with source location Unvailable Bed
        discharge_id = self.activity_pool.search(
            cr, uid, [['patient_id', '=', self.patients[4]],
                      ['data_model', '=', 'nh.clinical.patient.discharge']])
        self.activity_pool.cancel(cr, self.adt_uid, discharge_id[0])
        discharge = self.activity_pool.browse(cr, uid, discharge_id[0])
        self.assertNotEqual(discharge.parent_id.location_id.id,
                            discharge.data_ref.location_id.id)

        # prepare for cancel transfer
        ward_id = self.locations.keys()[2]
        wm_id = self.users[ward_id]['wm']
        bed_id = self.locations[ward_id][0]

        move_data = {
            'location_id': bed_id,
            'patient_id': self.patients[4]
        }
        move_id = self.move_pool.create_activity(cr, wm_id, {}, move_data)
        self.activity_pool.complete(cr, wm_id, move_id)

    def test_11_transfer_submit_complete(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Transfer a patient
        transfer_data = {
            'patient_id': self.patients[2],
            'location_id': self.locations.keys()[0]
        }
        transfer_id = self.transfer_pool.create_activity(
            cr, self.adt_uid, {}, transfer_data)
        self.activity_pool.complete(cr, self.adt_uid, transfer_id)
        transfer = self.activity_pool.browse(cr, uid, transfer_id)
        self.assertEqual(transfer.data_ref.location_id.id,
                         self.locations.keys()[0])
        self.assertEqual(transfer.data_ref.origin_loc_id.id,
                         self.locations.keys()[1])
        self.assertEqual(transfer.parent_id.data_model,
                         'nh.clinical.spell')
        self.assertEqual(transfer.parent_id.location_id.id,
                         self.locations.keys()[0])

        # Scenario 2: Transfer a patient to the same ward he/she is already in
        transfer_data = {
            'patient_id': self.patients[3],
            'location_id': self.locations.keys()[2]
        }
        transfer_id = self.transfer_pool.create_activity(
            cr, self.adt_uid, {}, transfer_data)
        self.activity_pool.complete(cr, self.adt_uid, transfer_id)
        transfer = self.activity_pool.browse(cr, uid, transfer_id)
        self.assertNotEqual(transfer.parent_id.location_id.id,
                            self.locations.keys()[2])

        # Scenario 3: Transfer a patient without spell
        transfer_data = {
            'patient_id': self.patients[5],
            'location_id': self.locations.keys()[0]
        }
        with self.assertRaises(except_orm):
            self.transfer_pool.create_activity(cr, uid, {}, transfer_data)

        # Scenario 4: Transfer a patient without patient information
        transfer_data = {
            'location_id': self.locations.keys()[0]
        }
        with self.assertRaises(except_orm):
            self.transfer_pool.create_activity(cr, uid, {}, transfer_data)

        # prepare for cancel transfer
        transfer_data = {
            'patient_id': self.patients[4],
            'location_id': self.locations.keys()[0]
        }
        transfer_id = self.transfer_pool.create_activity(cr, self.adt_uid, {},
                                                         transfer_data)
        self.activity_pool.complete(cr, self.adt_uid, transfer_id)

        transfer_data = {
            'patient_id': self.patients[0],
            'location_id': self.locations.keys()[0]
        }
        transfer_id = self.transfer_pool.create_activity(cr, self.adt_uid, {},
                                                         transfer_data)
        self.activity_pool.complete(cr, self.adt_uid, transfer_id)

    def test_12_get_last_transfer(self):
        cr, uid = self.cr, self.uid

        transfer_id = self.activity_pool.search(
            cr, uid, [['patient_id', '=', self.patients[2]],
                      ['data_model', '=', 'nh.clinical.patient.transfer']])

        # Scenario 1: Transfer exists
        self.assertEqual(
            self.transfer_pool.get_last(cr, uid, self.patients[2]),
            transfer_id[0])

        # Scenario 2: Transfer does not exist
        self.assertFalse(
            self.transfer_pool.get_last(cr, uid, self.patients[1]))

        # Scenario 3: Exception 'True', Transfer exists
        with self.assertRaises(except_orm):
            self.transfer_pool.get_last(cr, uid, self.patients[2],
                                        exception='True')

        # Scenario 4: Exception 'False', Transfer does not exist
        with self.assertRaises(except_orm):
            self.transfer_pool.get_last(cr, uid, self.patients[1],
                                        exception='False')

    def test_13_transfer_cancel(self):
        cr, uid = self.cr, self.uid

        transfer_id = self.activity_pool.search(
            cr, uid, [['patient_id', '=', self.patients[2]],
                      ['data_model', '=', 'nh.clinical.patient.transfer']])

        # Scenario 1: Cancel a transfer
        self.activity_pool.cancel(cr, uid, transfer_id[0])
        transfer = self.activity_pool.browse(cr, uid, transfer_id[0])
        self.assertEqual(transfer.parent_id.location_id.id,
                         self.locations.keys()[1])

        transfer_id = self.activity_pool.search(
            cr, uid, [['patient_id', '=', self.patients[3]],
                      ['data_model', '=', 'nh.clinical.patient.transfer']])

        # Scenario 2:
        # Cancel a transfer from the same ward the patient is already in.
        self.activity_pool.cancel(cr, uid, transfer_id[0])
        transfer = self.activity_pool.browse(cr, uid, transfer_id[0])
        self.assertNotEqual(transfer.parent_id.location_id.id,
                            self.locations.keys()[2])

        # Scenario 3:
        # Cancel a transfer for a patient
        # which original location is now unavailable.
        ward_id = self.locations.keys()[2]
        wm_id = self.users[ward_id]['wm']
        bed_id = self.locations[ward_id][0]

        move_data = {
            'location_id': bed_id,
            'patient_id': self.patients[3]
        }
        move_id = self.move_pool.create_activity(cr, wm_id, {}, move_data)
        self.activity_pool.complete(cr, wm_id, move_id)

        transfer_id = self.activity_pool.search(
            cr, uid, [['patient_id', '=', self.patients[4]],
                      ['data_model', '=', 'nh.clinical.patient.transfer']])
        self.activity_pool.cancel(cr, uid, transfer_id[0])
        transfer = self.activity_pool.browse(cr, uid, transfer_id[0])
        self.assertEqual(transfer.parent_id.location_id.id, ward_id)

        # Scenario 4: Cancel transfer for non admitted / discharged patient
        discharge_data = {
            'patient_id': self.patients[0]
        }
        discharge_id = self.discharge_pool.create_activity(
            cr, self.adt_uid, {}, discharge_data)
        self.assertTrue(self.activity_pool.complete(cr, self.adt_uid,
                                                    discharge_id))
        transfer_id = self.activity_pool.search(
            cr, uid, [['patient_id', '=', self.patients[0]],
                      ['data_model', '=', 'nh.clinical.patient.transfer']])
        with self.assertRaises(except_orm):
            self.activity_pool.cancel(cr, uid, transfer_id[0])

    def test_14_patient_following(self):
        cr, uid = self.cr, self.uid

        ward_id = self.locations.keys()[0]
        wm_id = self.users[ward_id]['wm']
        nurse_id = self.users[ward_id]['n']

        # Creating 4 Patient Follow Activities:
        # 1) test Patient Follow.
        # 2) test open follow activities are cancelled
        # when 'unfollowing' a patient.
        # 3) test 2nd case only happens if you created those follow activities.
        follow_id = self.follow_pool.create_activity(
            cr, uid, {'user_id': nurse_id},
            {'patient_ids': [[4, self.patients[3]]]}
        )
        follow_id2 = self.follow_pool.create_activity(
            cr, uid, {'user_id': nurse_id},
            {'patient_ids': [[6, False, [self.patients[3], self.patients[4]]]]}
        )
        follow_id3 = self.follow_pool.create_activity(
            cr, wm_id, {'user_id': nurse_id},
            {'patient_ids': [[6, False, [self.patients[3], self.patients[4]]]]}
        )
        self.assertTrue(follow_id,
                        msg="Patient Follow: Create activity failed")
        self.assertTrue(follow_id2,
                        msg="Patient Follow: Create activity failed")
        self.assertTrue(follow_id3,
                        msg="Patient Follow: Create activity failed")

        # Complete Follow Activity and check System state POST-COMPLETE
        self.activity_pool.complete(cr, uid, follow_id)
        user = self.users_pool.browse(cr, uid, nurse_id)
        self.assertTrue(
            self.patients[3] in [patient.id for patient in user.following_ids],
            msg="Patient Follow: The user is not following that patient")
        self.assertFalse(
            self.patients[4] in [patient.id for patient in user.following_ids],
            msg="Patient Follow: "
                "The user should not be following that patient")
        patient = self.patient_pool.browse(cr, uid, self.patients[3])
        patient2 = self.patient_pool.browse(cr, uid, self.patients[4])
        self.assertTrue(nurse_id in [u.id for u in patient.follower_ids],
                        msg="Patient Follow: "
                            "The user is not in the patient followers list")
        self.assertFalse(
            nurse_id in [u.id for u in patient2.follower_ids],
            msg="Patient Follow: "
                "The user should not be in the patient followers list")

        # Create an Unfollow Activity
        unfollow_id = self.unfollow_pool.create_activity(
            cr, uid, {}, {'patient_ids': [[4, self.patients[3]]]})
        self.assertTrue(unfollow_id,
                        msg="Patient Unfollow: Create activity failed")

        # Complete Unfollow Activity and check System state POST-COMPLETE
        self.activity_pool.complete(cr, uid, unfollow_id)
        user = self.users_pool.browse(cr, uid, nurse_id)
        self.assertTrue(
            self.patients[3] not in [pat.id for pat in user.following_ids],
            msg="Patient Unfollow: The user is still following that patient")
        patient = self.patient_pool.browse(cr, uid, self.patients[3])
        self.assertTrue(
            nurse_id not in [u.id for u in patient.follower_ids],
            msg="Patient Unfollow: "
                "The user still is in the patient followers list")

        follow = self.activity_pool.browse(cr, uid, follow_id2)
        self.assertEqual(follow.state, 'cancelled',
                         msg="Patient Unfollow: A follow activity containing "
                             "the unfollowed patient was not cancelled")
        follow = self.activity_pool.browse(cr, uid, follow_id3)
        self.assertNotEqual(follow.state, 'cancelled',
                            msg="Patient Unfollow: A follow activity created "
                                "by a different user was cancelled")

        # Try to complete follow activity without user assigned to it
        follow_id = self.follow_pool.create_activity(
            cr, uid, {}, {'patient_ids': [[4, self.patients[3]]]})
        with self.assertRaises(except_orm):
            self.activity_pool.complete(cr, uid, follow_id)
