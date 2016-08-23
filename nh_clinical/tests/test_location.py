# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import logging

from faker import Faker
from openerp.tests import common
from openerp.osv.orm import except_orm


_logger = logging.getLogger(__name__)

fake = Faker()


class TestLocation(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestLocation, cls).setUpClass()
        cr, uid = cls.cr, cls.uid
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.patient_pool = cls.registry('nh.clinical.patient')
        cls.activity_pool = cls.registry('nh.activity')
        cls.spell_pool = cls.registry('nh.clinical.spell')
        cls.placement_pool = cls.registry('nh.clinical.patient.placement')
        cls.user_pool = cls.registry('res.users')
        cls.group_pool = cls.registry('res.groups')
        cls.context_pool = cls.registry('nh.clinical.context')
        cls.category_pool = cls.registry('res.partner.category')

        cls.contexts = []
        cls.contexts.append(cls.context_pool.create(
            cr, uid, {'name': 'c0', 'models': '[]'}))
        cls.contexts.append(cls.context_pool.create(
            cr, uid, {'name': 'c1', 'models': "['nh.clinical.location']"}))
        cls.hospital_id = cls.location_pool.create(
            cr, uid, {'name': 'Test Hospital', 'code': 'TESTHOSP'})
        cls.pos_id = cls.pos_pool.create(
            cr, uid, {'name': 'Test POS', 'location_id': cls.hospital_id})
        cls.admin_role_id = cls.category_pool.search(
            cr, uid, [['name', '=', 'System Administrator']])[0]
        group_ids = cls.group_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Admin Group']])
        cls.hca_group_id = cls.group_pool.search(
            cr, uid, [['name', '=', 'NH Clinical HCA Group']])[0]
        cls.nurse_group_id = cls.group_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Nurse Group']])[0]
        cls.admin_id = cls.user_pool.create(
            cr, uid, {'name': 'Test User', 'login': 'user_001',
                      'password': 'user_001', 'groups_id': [[4, group_ids[0]]],
                      'category_id': [[4, cls.admin_role_id]],
                      'pos_ids': [[6, 0, [cls.pos_id]]]})
        cls.hca_uid = cls.user_pool.create(
            cr, uid, {'name': 'HCA01', 'login': 'hca01', 'password': 'hca01',
                      'groups_id': [[4, cls.hca_group_id]]})
        cls.nurse_uid = cls.user_pool.create(
            cr, uid, {'name': 'Nurse01', 'login': 'nurse01',
                      'password': 'nurse01',
                      'groups_id': [[4, cls.nurse_group_id]]})
        cls.ward_id = cls.location_pool.create(
            cr, uid, {'name': 'Ward0', 'code': 'W0', 'usage': 'ward',
                      'parent_id': cls.hospital_id, 'type': 'poc',
                      'context_ids': [[6, 0, [cls.contexts[1]]]]})
        cls.bed_id = cls.location_pool.create(
            cr, uid, {'name': 'Bed0', 'code': 'B0', 'usage': 'bed',
                      'parent_id': cls.ward_id, 'type': 'poc'})

        cls.patients = [
            cls.patient_pool.create(
                cr, uid,
                {
                    'family_name': 'Testersen',
                    'given_name': 'Test'+str(i),
                    'other_identifier': 'TESTHN00'+str(i)}) for i in range(4)
        ]

    def test_01_create(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Create a new Location
        location_id = self.location_pool.create(
            cr, uid, {'name': 'Test Loc', 'code': 'TESTLOC01'})
        self.assertTrue(location_id, msg="Location create failed")
        location = self.location_pool.browse(cr, uid, location_id)
        self.assertTrue(location.active, msg="Location created is not active")
        self.assertEqual(location.patient_capacity, 1,
                         msg="Location default capacity not set")
        self.assertEqual(location.name, 'Test Loc',
                         msg="Location name not set")

    def test_02_get_pos_id(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Create a new Location with a POS assigned to it
        location_id = self.location_pool.create(
            cr, uid, {'name': 'Test Loc', 'code': 'TESTLOC02'})
        pos_id = self.pos_pool.create(
            cr, uid, {'name': 'Test POS', 'location_id': location_id})
        result = self.location_pool._get_pos_id(cr, uid, location_id,
                                                field='pos_id', args={})
        self.assertEqual(result[location_id], pos_id,
                         msg="POS not assigned correctly to the Location")

        # Scenario 2:
        # Create a new Location child of the 1st one. POS should be the same.
        location2_id = self.location_pool.create(
            cr, uid, {'name': 'Test Loc', 'code': 'TESTLOC03',
                      'parent_id': location_id})
        result = self.location_pool._get_pos_id(cr, uid, location2_id,
                                                field='pos_id', args={})
        self.assertEqual(result[location2_id], pos_id,
                         msg="POS not assigned correctly to the Location")

        # Scenario 3:
        # Create a new Location not related to the others.
        # POS should be not set.
        location_id = self.location_pool.create(
            cr, uid, {'name': 'Test Loc', 'code': 'TESTLOC04'})
        result = self.location_pool._get_pos_id(cr, uid, location_id,
                                                field='pos_id', args={})
        self.assertEqual(result[location_id], False,
                         msg="POS assigned incorrectly to the Location")

    def test_03_get_available_location_ids(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Create a new Location and check its returned
        location_id = self.location_pool.create(
            cr, uid, {'name': 'Test Loc', 'code': 'TESTLOC05', 'type': 'poc',
                      'usage': 'bed'})
        pos_id = self.pos_pool.create(
            cr, uid, {'name': 'Test POS', 'location_id': location_id})
        result = self.location_pool.get_available_location_ids(cr, uid)
        self.assertTrue(location_id in result,
                        msg="Location not found in Available Locations")

        # Scenario 2: Make the location unavailable
        self.patient_pool.write(cr, uid, self.patients[0],
                                {'current_location_id': location_id})
        activity_id = self.spell_pool.create_activity(
            cr, uid, {}, {'patient_id': self.patients[0],
                          'location_id': location_id, 'pos_id': pos_id})
        self.activity_pool.start(cr, uid, activity_id)
        result = self.location_pool.get_available_location_ids(cr, uid)
        self.assertFalse(location_id in result,
                         msg="Location found in Available Locations")

    def test_04_is_available(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Create a new Location and check its availability
        location_id = self.location_pool.create(
            cr, uid, {'name': 'Test Loc', 'code': 'TESTLOC06', 'type': 'poc',
                      'usage': 'bed'})
        pos_id = self.pos_pool.create(
            cr, uid, {'name': 'Test POS', 'location_id': location_id})
        result = self.location_pool._is_available(cr, uid, [location_id],
                                                  field='is_available',
                                                  args={})
        self.assertTrue(result[location_id],
                        msg="Availability not set correctly")

        # Scenario 2: Assign a patient to the location
        self.patient_pool.write(cr, uid, self.patients[1],
                                {'current_location_id': location_id})
        result = self.location_pool._is_available(cr, uid, [location_id],
                                                  field='is_available',
                                                  args={})
        self.assertTrue(result[location_id],
                        msg="Availability updated incorrectly "
                            "when patient is linked to it")

        # Scenario 3: Assign a spell to the location
        self.patient_pool.write(cr, uid, self.patients[1],
                                {'current_location_id': False})
        activity_id = self.spell_pool.create_activity(
            cr, uid, {}, {'patient_id': self.patients[1],
                          'location_id': location_id, 'pos_id': pos_id})
        result = self.location_pool._is_available(cr, uid, [location_id],
                                                  field='is_available',
                                                  args={})
        self.assertTrue(result[location_id],
                        msg="Availability updated incorrectly "
                            "when spell is linked to it")

        # Scenario 4: Start the spell
        self.activity_pool.start(cr, uid, activity_id)
        result = self.location_pool._is_available(cr, uid, [location_id],
                                                  field='is_available',
                                                  args={})
        self.assertFalse(result[location_id],
                         msg="Availability not updated correctly "
                             "when spell is started")

        # Scenario 5: Complete the spell
        self.activity_pool.complete(cr, uid, activity_id)
        result = self.location_pool._is_available(cr, uid, [location_id],
                                                  field='is_available',
                                                  args={})
        self.assertTrue(result[location_id],
                        msg="Availability not updated correctly "
                            "when spell is completed")

        # Scenario 6: Cancel the spell
        self.activity_pool.cancel(cr, uid, activity_id)
        result = self.location_pool._is_available(cr, uid, [location_id],
                                                  field='is_available',
                                                  args={})
        self.assertTrue(result[location_id],
                        msg="Availability not updated correctly "
                            "when spell is cancelled")

        # Scenario 7: Create a new Ward Location and check its availability
        location_id = self.location_pool.create(
            cr, uid, {'name': 'Test Loc', 'code': 'TESTLOC07', 'type': 'poc',
                      'usage': 'ward'})
        pos_id = self.pos_pool.create(
            cr, uid, {'name': 'Test POS', 'location_id': location_id})
        result = self.location_pool._is_available(cr, uid, [location_id],
                                                  field='is_available',
                                                  args={})
        self.assertTrue(result[location_id],
                        msg="Availability not set correctly")

        # Scenario 8: Assign the location to an started Spell
        self.patient_pool.write(cr, uid, self.patients[2],
                                {'current_location_id': location_id})
        activity_id = self.spell_pool.create_activity(
            cr, uid, {}, {'patient_id': self.patients[2],
                          'location_id': location_id, 'pos_id': pos_id})
        self.activity_pool.start(cr, uid, activity_id)
        result = self.location_pool._is_available(cr, uid, [location_id],
                                                  field='is_available',
                                                  args={})
        self.assertTrue(result[location_id],
                        msg="Availability updated incorrectly "
                            "when spell is started")

    def test_05_get_patient_ids(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Create a new Location and check its patients
        location_id = self.location_pool.create(
            cr, uid, {'name': 'Test Loc', 'code': 'TESTLOC08', 'type': 'poc',
                      'usage': 'ward'})
        pos_id = self.pos_pool.create(
            cr, uid, {'name': 'Test POS', 'location_id': location_id})
        result = self.location_pool._get_patient_ids(cr, uid, location_id,
                                                     field='patient_ids',
                                                     args={})
        self.assertFalse(result[location_id],
                         msg="Patients returned for a location "
                             "without patients")

        # Scenario 2: Create a new Patient and assign it to the location
        self.patient_pool.write(cr, uid, self.patients[0],
                                {'current_location_id': location_id})
        result = self.location_pool._get_patient_ids(cr, uid, location_id,
                                                     field='patient_ids',
                                                     args={})
        self.assertTrue(self.patients[0] in result[location_id],
                        msg="Patient not found in result")

        # Scenario 3: Create a new Patient and assign it to a child location
        location2_id = self.location_pool.create(
            cr, uid, {'name': 'Test Loc', 'code': 'TESTLOC09', 'type': 'poc',
                      'usage': 'bed', 'parent_id': location_id})
        self.patient_pool.write(cr, uid, self.patients[1],
                                {'current_location_id': location2_id})
        result = self.location_pool._get_patient_ids(cr, uid, location_id,
                                                     field='patient_ids',
                                                     args={})
        self.assertTrue(self.patients[0] in result[location_id],
                        msg="Patient not found in result")
        self.assertTrue(self.patients[1] in result[location_id],
                        msg="Patient not found in result")

        # Scenario 4:
        # Create a new Patient, create his spell and
        # assign the spell to the location.
        self.patient_pool.write(cr, uid, self.patients[2],
                                {'current_location_id': False})
        spell_id = self.spell_pool.get_by_patient_id(cr, uid, self.patients[2])
        self.spell_pool.write(cr, uid, spell_id,
                              {'location_id': location_id, 'pos_id': pos_id})
        result = self.location_pool._get_patient_ids(cr, uid, location_id,
                                                     field='patient_ids',
                                                     args={})
        self.assertFalse(self.patients[2] in result[location_id],
                         msg="Unexpected patient found in result")

        # Scenario 5: Test _get_child_patients
        result = self.location_pool._get_child_patients(cr, uid, location_id,
                                                        field='child_patients',
                                                        args={})
        self.assertEqual(result[location_id], 1,
                         msg="Wrong number of patients returned")

    def test_06_get_users_from_location(self):
        """
        Test _get_user_ids and the other methods related to
        getting users from the location.
        SETUP: location_id is a Ward with room_id and bed_id as child locations
            hca_user_id is a HCA user assigned to the ward
            hca_user2_id is a HCA user assigned to the bed
            nurse_user_id is a Nurse user assigned to the ward
            nurse_user2_id is a Nurse user assigned to the bed
            wm_user_id is a Ward Manager user assigned to the ward
            wm_user2_id is a Ward Manager user assigned to the bed
            doctor_user_id is a Doctor user assigned to the ward
            doctor_user2_id is a Doctor user assigned to the bed
            junior_user_id is a Junior Doctor user assigned to the ward
            consultant_user_id is a Consultant user assigned to the ward
            registrar_user_id is a Registrar user assigned to the ward
        """
        cr, uid = self.cr, self.uid

        # Creating Locations
        location_id = self.location_pool.create(
            cr, uid, {'name': 'Test Loc', 'code': 'TESTLOC10', 'type': 'poc',
                      'usage': 'ward'})
        room_id = self.location_pool.create(
            cr, uid, {'name': 'Test Room', 'code': 'TESTLOC11',
                      'type': 'structural', 'usage': 'room',
                      'parent_id': location_id})
        bed_id = self.location_pool.create(
            cr, uid, {'name': 'Test Bed', 'code': 'TESTLOC12', 'type': 'poc',
                      'usage': 'bed', 'parent_id': room_id})

        # Creating HCA users
        hca_group_id = self.group_pool.search(
            cr, uid, [['name', '=', 'NH Clinical HCA Group']])
        hca_user_id = self.user_pool.create(
            cr, uid, {'name': 'Test HCA', 'login': 'testhca',
                      'groups_id': [[6, 0, hca_group_id]],
                      'location_ids': [[6, 0, [location_id]]]})
        hca_user2_id = self.user_pool.create(
            cr, uid, {'name': 'Test HCA 2', 'login': 'testhca2',
                      'groups_id': [[6, 0, hca_group_id]],
                      'location_ids': [[6, 0, [bed_id]]]})

        # Creating Nurse users
        nurse_group_id = self.group_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Nurse Group']])
        nurse_user_id = self.user_pool.create(
            cr, uid, {'name': 'Test Nurse', 'login': 'testnurse',
                      'groups_id': [[6, 0, nurse_group_id]],
                      'location_ids': [[6, 0, [location_id]]]})
        nurse_user2_id = self.user_pool.create(
            cr, uid, {'name': 'Test Nurse 2', 'login': 'testnurse2',
                      'groups_id': [[6, 0, nurse_group_id]],
                      'location_ids': [[6, 0, [bed_id]]]})

        # Creating Ward Manager users
        wm_group_id = self.group_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Shift Coordinator Group']])
        wm_user_id = self.user_pool.create(
            cr, uid, {'name': 'Test Shift Coordinator', 'login': 'testwm',
                      'groups_id': [[6, 0, wm_group_id]],
                      'location_ids': [[6, 0, [location_id]]]})
        wm_user2_id = self.user_pool.create(
            cr, uid, {'name': 'Test Shift Coordinator 2', 'login': 'testwm2',
                      'groups_id': [[6, 0, wm_group_id]],
                      'location_ids': [[6, 0, [bed_id]]]})

        # Creating Doctor users
        doctor_group_id = self.group_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Doctor Group']])
        doctor_user_id = self.user_pool.create(
            cr, uid, {'name': 'Test Doctor', 'login': 'testdoctor',
                      'groups_id': [[6, 0, doctor_group_id]],
                      'location_ids': [[6, 0, [location_id]]]})
        junior_group_id = self.group_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Junior Doctor Group']])
        junior_user_id = self.user_pool.create(
            cr, uid, {'name': 'Test Junior Doctor', 'login': 'testjunior',
                      'groups_id': [[6, 0, junior_group_id]],
                      'location_ids': [[6, 0, [location_id]]]})
        consultant_group_id = self.group_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Consultant Group']])
        consultant_user_id = self.user_pool.create(
            cr, uid, {'name': 'Test Consultant', 'login': 'testconsultant',
                      'groups_id': [[6, 0, consultant_group_id]],
                      'location_ids': [[6, 0, [location_id]]]})
        registrar_group_id = self.group_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Registrar Group']])
        registrar_user_id = self.user_pool.create(
            cr, uid, {'name': 'Test Registrar', 'login': 'testregistrar',
                      'groups_id': [[6, 0, registrar_group_id]],
                      'location_ids': [[6, 0, [location_id]]]})
        doctor_user2_id = self.user_pool.create(
            cr, uid, {'name': 'Test Doctor 2', 'login': 'testdoctor2',
                      'groups_id': [[6, 0, doctor_group_id]],
                      'location_ids': [[6, 0, [bed_id]]]})
        all_user_ids = [hca_user_id, hca_user2_id, nurse_user_id,
                        nurse_user2_id, wm_user_id, wm_user2_id,
                        doctor_user_id, doctor_user2_id, junior_user_id,
                        consultant_user_id, registrar_user_id]
        bed_assigned_user_ids = [hca_user2_id, nurse_user2_id, wm_user2_id,
                                 doctor_user2_id]

        # Scenario 1: _get_user_ids test
        # 1.1 Test every user is returned
        # when looking for all users within the location.
        result = self.location_pool._get_user_ids(cr, uid, location_id)
        for user_id in all_user_ids:
            self.assertTrue(user_id in result,
                            msg="user %s not returned" % user_id)

        # 1.2 Test bed assigned users are not returned
        #  when turning the recursive search OFF.
        result = self.location_pool._get_user_ids(cr, uid, location_id,
                                                  recursive=False)
        for user_id in all_user_ids:
            if user_id in bed_assigned_user_ids:
                self.assertFalse(user_id in result,
                                 msg="bed assigned user %s returned" % user_id)
            else:
                self.assertTrue(user_id in result,
                                msg="user %s not returned" % user_id)
        # 1.3 Test specific group search returns only users from that group
        result = self.location_pool._get_user_ids(
            cr, uid, location_id, group_names=['NH Clinical Nurse Group'])
        for user_id in all_user_ids:
            if user_id in [nurse_user_id, nurse_user2_id]:
                self.assertTrue(user_id in result,
                                msg="Nurse user %s not returned" % user_id)
            else:
                self.assertFalse(user_id in result,
                                 msg="user %s returned" % user_id)

        # Scenario 2: Test _get_hca_ids method.
        # Returns HCA users for the location (recursively).
        result = self.location_pool._get_hca_ids(
            cr, uid, location_id, field='assigned_hca_ids', args={})
        self.assertTrue(hca_user_id in result[location_id],
                        msg="HCA not found in result")
        self.assertTrue(hca_user2_id in result[location_id],
                        msg="HCA assigned to bed not found in result")

        # Scenario 3: Test _get_hcas method.
        # Returns the number of HCA users for the location (recursively).
        result = self.location_pool._get_hcas(cr, uid, location_id,
                                              field='related_hcas', args={})
        self.assertEqual(result[location_id], 2,
                         msg="Wrong number of HCA users returned")

        # Scenario 4: Test _get_nurse_ids method.
        # Returns Nurse users for the location (recursively).
        result = self.location_pool._get_nurse_ids(cr, uid, location_id,
                                                   field='assigned_nurse_ids',
                                                   args={})
        self.assertTrue(nurse_user_id in result[location_id],
                        msg="Nurse not found in result")
        self.assertTrue(nurse_user2_id in result[location_id],
                        msg="Nurse assigned to bed not found in result")

        # Scenario 5: Test _get_nurses method.
        # Returns the number of Nurse users for the location (recursively).
        result = self.location_pool._get_nurses(cr, uid, location_id,
                                                field='related_nurses',
                                                args={})
        self.assertEqual(result[location_id], 2,
                         msg="Wrong number of Nurse users returned")

        # Scenario 6: Test _get_wm_ids method.
        # Returns Ward Manager users for the location
        # if the location is a ward it will do it NOT recursively.
        # Recursively in any other case.
        result = self.location_pool._get_wm_ids(cr, uid, location_id,
                                                field='assigned_wm_ids',
                                                args={})
        self.assertTrue(wm_user_id in result[location_id],
                        msg="Shift Coordinator not found in result")
        self.assertFalse(
            wm_user2_id in result[location_id],
            msg="Shift Coordinator assigned to bed found in result"
        )
        result = self.location_pool._get_wm_ids(cr, uid, room_id,
                                                field='assigned_wm_ids',
                                                args={})
        self.assertTrue(
            wm_user2_id in result[room_id],
            msg="Shift Coordinator assigned to bed not found in result"
        )

        # Scenario 7: Test _get_doctor_ids method.
        # Returns any users in the doctor groups for the location (recursively)
        # Doctor groups are: Doctor, Junior Doctor, Consultant and Registrar.
        result = self.location_pool._get_doctor_ids(
            cr, uid, location_id, field='assigned_doctor_ids', args={})
        self.assertTrue(doctor_user_id in result[location_id],
                        msg="Doctor not found in result")
        self.assertTrue(junior_user_id in result[location_id],
                        msg="Junior Doctor not found in result")
        self.assertTrue(consultant_user_id in result[location_id],
                        msg="Consultant not found in result")
        self.assertTrue(registrar_user_id in result[location_id],
                        msg="Registrar not found in result")
        self.assertTrue(doctor_user2_id in result[location_id],
                        msg="Doctor assigned to bed not found in result")

    def test_07_get_waiting_patients(self):
        cr, uid = self.cr, self.uid

        location_id = self.location_pool.create(
            cr, uid, {'name': 'Test Loc', 'code': 'TESTLOC13', 'type': 'poc',
                      'usage': 'ward'})
        pos_id = self.pos_pool.create(
            cr, uid, {'name': 'Test POS', 'location_id': location_id})
        bed_id = self.location_pool.create(
            cr, uid, {'name': 'Test Bed', 'code': 'TESTLOC14', 'type': 'poc',
                      'usage': 'bed', 'parent_id': location_id})

        spell_id = self.spell_pool.get_by_patient_id(cr, uid, self.patients[2])
        self.spell_pool.write(cr, uid, spell_id,
                              {'location_id': location_id, 'pos_id': pos_id})
        placement_id = self.placement_pool.create_activity(
            cr, uid, {}, {'suggested_location_id': location_id,
                          'patient_id': self.patients[2]})

        # Scenario 1: Get related patients
        result = self.location_pool._get_waiting_patients(
            cr, uid, location_id, field='waiting_patients', args={})
        self.assertEqual(result[location_id], 1,
                         msg="Wrong number of related patients")

        # Scenario 2: Complete the placement
        self.activity_pool.submit(cr, uid, placement_id,
                                  {'location_id': bed_id})
        self.activity_pool.complete(cr, uid, placement_id)
        result = self.location_pool._get_waiting_patients(
            cr, uid, location_id, field='waiting_patients', args={})
        self.assertEqual(result[location_id], 0,
                         msg="Wrong number of related patients")

    def test_08_get_closest_parent_id(self):
        cr, uid = self.cr, self.uid
        # Set Up Ward parent of Bay parent of Room parent of Bed
        ward_id = self.location_pool.create(
            cr, uid, {'name': 'Test Ward', 'code': 'TESTLOC15', 'type': 'poc',
                      'usage': 'ward'})
        bay_id = self.location_pool.create(
            cr, uid, {'name': 'Test Bay', 'code': 'TESTLOC16', 'type': 'poc',
                      'usage': 'bay', 'parent_id': ward_id})
        room_id = self.location_pool.create(
            cr, uid, {'name': 'Test Room', 'code': 'TESTLOC17',
                      'type': 'structural', 'usage': 'room',
                      'parent_id': bay_id})
        bed_id = self.location_pool.create(
            cr, uid, {'name': 'Test Bed', 'code': 'TESTLOC18', 'type': 'poc',
                      'usage': 'bed', 'parent_id': room_id})

        # Scenario 1: Test 1 level deep relationships.
        self.assertEqual(
            room_id,
            self.location_pool.get_closest_parent_id(cr, uid, bed_id, 'room'))
        self.assertEqual(
            bay_id,
            self.location_pool.get_closest_parent_id(cr, uid, room_id, 'bay'))
        self.assertEqual(
            ward_id,
            self.location_pool.get_closest_parent_id(cr, uid, bay_id, 'ward'))

        # Scenario 2: Test recursive cases.
        self.assertEqual(
            bay_id,
            self.location_pool.get_closest_parent_id(cr, uid, bed_id, 'bay'))
        self.assertEqual(
            ward_id,
            self.location_pool.get_closest_parent_id(cr, uid, bed_id, 'ward'))
        self.assertEqual(
            ward_id,
            self.location_pool.get_closest_parent_id(cr, uid, room_id, 'ward'))

        # Scenario 3:
        # Test False is returned when there is no parent with required usage.
        self.assertFalse(
            self.location_pool.get_closest_parent_id(cr, uid, bed_id, 'bed'),
            msg="Found an unexpected parent location")
        self.assertFalse(
            self.location_pool.get_closest_parent_id(cr, uid, room_id, 'bed'),
            msg="Found an unexpected parent location")
        self.assertFalse(
            self.location_pool.get_closest_parent_id(cr, uid, bay_id, 'room'),
            msg="Found an unexpected parent location")
        self.assertFalse(
            self.location_pool.get_closest_parent_id(cr, uid, ward_id, 'ward'),
            msg="Found an unexpected parent location")

    def test_09_is_child_of(self):
        cr, uid = self.cr, self.uid

        ward_id = self.location_pool.search(cr, uid,
                                            [['code', '=', 'TESTLOC15']])[0]
        bay_id = self.location_pool.search(cr, uid,
                                           [['code', '=', 'TESTLOC16']])[0]
        room_id = self.location_pool.search(cr, uid,
                                            [['code', '=', 'TESTLOC17']])[0]
        bed_id = self.location_pool.search(cr, uid,
                                           [['code', '=', 'TESTLOC18']])[0]

        # Scenario 1: Test 0 level deep relationships.
        self.assertTrue(self.location_pool.is_child_of(cr, uid, bed_id,
                                                       'TESTLOC18'))
        self.assertTrue(self.location_pool.is_child_of(cr, uid, room_id,
                                                       'TESTLOC17'))
        self.assertTrue(self.location_pool.is_child_of(cr, uid, bay_id,
                                                       'TESTLOC16'))
        self.assertTrue(self.location_pool.is_child_of(cr, uid, ward_id,
                                                       'TESTLOC15'))

        # Scenario 2: Test 1 level deep relationships.
        self.assertTrue(self.location_pool.is_child_of(cr, uid, bed_id,
                                                       'TESTLOC17'))
        self.assertTrue(self.location_pool.is_child_of(cr, uid, room_id,
                                                       'TESTLOC16'))
        self.assertTrue(self.location_pool.is_child_of(cr, uid, bay_id,
                                                       'TESTLOC15'))

        # Scenario 3: Test X level deep relationships.
        self.assertTrue(self.location_pool.is_child_of(cr, uid, bed_id,
                                                       'TESTLOC15'))
        self.assertTrue(self.location_pool.is_child_of(cr, uid, room_id,
                                                       'TESTLOC15'))
        self.assertTrue(self.location_pool.is_child_of(cr, uid, bay_id,
                                                       'TESTLOC15'))

        # Scenario 3: Test False cases.
        self.assertFalse(self.location_pool.is_child_of(cr, uid, room_id,
                                                        'TESTLOC18'))
        self.assertFalse(self.location_pool.is_child_of(cr, uid, bay_id,
                                                        'TESTLOC17'))
        self.assertFalse(self.location_pool.is_child_of(cr, uid, ward_id,
                                                        'TESTLOC16'))

    def test_10_get_by_code(self):
        cr, uid = self.cr, self.uid

        ward_id = self.location_pool.search(
            cr, uid, [['code', '=', 'TESTLOC15']])[0]

        # Scenario 1: Test location id is returned.
        self.assertEqual(self.location_pool.get_by_code(cr, uid, 'TESTLOC15'),
                         ward_id, msg="Wrong id returned")

        # Scenario 2: Test False is returned when location does not exist.
        self.assertFalse(self.location_pool.get_by_code(cr, uid, 'TESTERROR'),
                         msg="Wrong return value when location is not found")

        # Scenario 3: Test a new ward is created when auto_create is True.
        location_id = self.location_pool.get_by_code(cr, self.admin_id,
                                                     'TESTLOC99',
                                                     auto_create=True)
        self.assertTrue(location_id,
                        msg="No location created with auto_create True")
        location = self.location_pool.read(cr, uid, location_id,
                                           ['name', 'code', 'pos_id',
                                            'parent_id', 'usage'])
        self.assertEqual(location['name'], 'TESTLOC99',
                         msg="Wrong location name")
        self.assertEqual(location['code'], 'TESTLOC99',
                         msg="Wrong location code")
        self.assertEqual(location['pos_id'][0], self.pos_id, msg="Wrong pos")
        self.assertEqual(location['parent_id'][0], self.hospital_id,
                         msg="Wrong parent location")
        self.assertEqual(location['usage'], 'ward', msg="Wrong location usage")

    def test_11_get_name(self):
        cr, uid = self.cr, self.uid

        ward_id = self.location_pool.create(
            cr, uid, {'name': 'Test Ward', 'code': 'TESTLOC19', 'type': 'poc',
                      'usage': 'ward'})
        room_id = self.location_pool.create(
            cr, uid, {'name': 'Test Room', 'code': 'TESTLOC20',
                      'type': 'structural', 'usage': 'room',
                      'parent_id': ward_id})
        bed_id = self.location_pool.create(
            cr, uid, {'name': 'Test Bed', 'code': 'TESTLOC21', 'type': 'poc',
                      'usage': 'bed', 'parent_id': room_id})
        bed2_id = self.location_pool.create(
            cr, uid, {'name': 'Test Bed 2', 'code': 'TESTLOC22', 'type': 'poc',
                      'usage': 'bed'})

        # Scenario 1: Ward name is the same as name field.
        result = self.location_pool._get_name(
            cr, uid, [ward_id, room_id, bed_id, bed2_id],
            field='full_name', args={})
        self.assertEqual('Test Ward', result[ward_id])

        # Scenario 2: Room name. 1 level deep of parent-child relationship.
        self.assertEqual('Test Room [Test Ward]', result[room_id])

        # Scenario 3: Bed name. Recursive level of parent-child relationship.
        self.assertEqual('Test Bed [Test Ward]', result[bed_id])

        # Scenario 4: 2nd Bed name. No Ward as parent.
        self.assertEqual('Test Bed 2', result[bed2_id])

    def test_12_is_available_search(self):
        cr, uid = self.cr, self.uid

        # Set up: create a location and make it unavailable
        location_id = self.location_pool.create(
            cr, uid, {'name': 'Test Loc', 'code': 'TESTLOC23', 'type': 'poc',
                      'usage': 'bed'})
        pos_id = self.pos_pool.create(cr, uid, {'name': 'Test POS',
                                                'location_id': location_id})
        activity_id = self.spell_pool.create_activity(
            cr, uid, {}, {'patient_id': self.patients[3],
                          'location_id': location_id, 'pos_id': pos_id})
        self.activity_pool.start(cr, uid, activity_id)
        # Scenario 1: Search for unavailable locations
        result = self.location_pool._is_available_search(
            cr, uid, obj='nh.clinical.location', name='Location',
            args=[['is_available', '=', False]])
        self.assertTrue(location_id in result[0][2],
                        msg="Location not found in unavailable locations")

        # Scenario 2: Search for available locations
        result = self.location_pool._is_available_search(
            cr, uid, obj='nh.clinical.location', name='Location',
            args=[['is_available', '!=', False]])
        self.assertFalse(location_id in result[0][2],
                         msg="Location found in available locations")

        # Scenario 3: Search for availability with not allowed operators
        result = self.location_pool._is_available_search(
            cr, uid, obj='nh.clinical.location', name='Location',
            args=[['is_available', '>', 2], ['is_available', '<', 'a']])
        self.assertEqual(
            [], result[0][2],
            msg="Search returned results with wrong operators")

    def test_13_switch_active_status(self):
        cr, uid = self.cr, self.uid

        location_id = self.location_pool.create(
            cr, uid, {'name': 'Test Loc', 'code': 'TESTLOC24', 'type': 'poc',
                      'usage': 'ward'})

        # Scenario 1: Deactivate a location
        self.assertTrue(self.location_pool.switch_active_status(
            cr, uid, location_id), msg="Switch active status failed")
        location = self.location_pool.browse(cr, uid, location_id)
        self.assertFalse(location.active, msg="Active value not updated")

        # Scenario 2: Activate a location
        self.assertTrue(self.location_pool.switch_active_status(
            cr, uid, location_id), msg="Switch active status failed")
        location = self.location_pool.browse(cr, uid, location_id)
        self.assertTrue(location.active, msg="Active value not updated")

    def test_14_get_nurse_follower_ids(self):
        cr, uid = self.cr, self.uid

        # Scenario 1:
        # Check followers without nurses following patients in that location.
        res = self.location_pool._get_nurse_follower_ids(
            cr, uid, [self.bed_id], 'nurse_follower_ids', None)
        self.assertFalse(res[self.bed_id])

        # Scenario 2:
        # Check followers when a nurse is following a patient in that location.
        self.patient_pool.write(cr, uid, self.patients[3],
                                {'current_location_id': self.bed_id})
        self.user_pool.write(cr, uid, self.nurse_uid,
                             {'following_ids': [[4, self.patients[3]]]})
        res = self.location_pool._get_nurse_follower_ids(
            cr, uid, [self.bed_id], 'nurse_follower_ids', None)
        self.assertListEqual(res[self.bed_id], [self.nurse_uid])

    def test_15_get_hca_follower_ids(self):
        cr, uid = self.cr, self.uid

        # Scenario 1:
        # Check followers without HCAs following patients in that location.
        res = self.location_pool._get_hca_follower_ids(
            cr, uid, [self.bed_id], 'hca_follower_ids', None)
        self.assertFalse(res[self.bed_id])

        # Scenario 2:
        # Check followers when a HCA is following a patient in that location.
        self.user_pool.write(cr, uid, self.hca_uid,
                             {'following_ids': [[4, self.patients[3]]]})
        res = self.location_pool._get_hca_follower_ids(
            cr, uid, [self.bed_id], 'hca_follower_ids', None)
        self.assertListEqual(res[self.bed_id], [self.hca_uid])

    def test_16_context_check_model(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: model is applicable on the specified context
        self.assertTrue(self.context_pool.check_model(
            cr, uid, self.contexts[1], 'nh.clinical.location'))

        # Scenario 2: model is not applicable on the specified context
        with self.assertRaises(except_orm):
            self.context_pool.check_model(cr, uid, self.contexts[0],
                                          'nh.clinical.location')

    def test_17_check_context_ids(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Use Add code
        self.assertTrue(self.location_pool.check_context_ids(
            cr, uid, [[4, self.contexts[1]]]))

        # Scenario 2: Use Replace code
        self.assertTrue(self.location_pool.check_context_ids(
            cr, uid, [[6, 0, [self.contexts[1]]]]))

        # Scenario 3: Use Remove code
        self.assertTrue(self.location_pool.check_context_ids(
            cr, uid, [[5, self.contexts[1]]]))

        # Scenario 4: Use List
        self.assertTrue(self.location_pool.check_context_ids(
            cr, uid, [self.contexts[1]]))

    def test_18_create_hospital_as_nhc_admin_generates_pos(self):
        cr, uid = self.cr, self.uid
        self.location_pool.create(cr, self.admin_id, {
            'name': 'Hospital 0', 'code': 'H0',
            'type': 'pos', 'usage': 'hospital'
        })
        pos_id = self.pos_pool.search(cr, uid, [['name', '=', 'Hospital 0']])
        self.assertTrue(pos_id)
        admin = self.user_pool.browse(cr, uid, self.admin_id)
        self.assertIn(pos_id[0], [p.id for p in admin.pos_ids])

    def test_19_create_hospital_as_non_nhc_admin_doesnt_generate_pos(self):
        cr, uid = self.cr, self.uid
        self.location_pool.create(cr, uid, {
            'name': 'Hospital 1', 'code': 'H1',
            'type': 'pos', 'usage': 'hospital'
        })
        pos_id = self.pos_pool.search(cr, uid, [['name', '=', 'Hospital 1']])
        self.assertFalse(pos_id)
