# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import logging

from openerp.tests.common import SingleTransactionCase
from openerp.osv.orm import except_orm

_logger = logging.getLogger(__name__)


class TestDevices(SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestDevices, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.user_pool = cls.registry('res.users')
        cls.groups_pool = cls.registry('res.groups')
        cls.partner_pool = cls.registry('res.partner')
        cls.activity_pool = cls.registry('nh.activity')
        cls.patient_pool = cls.registry('nh.clinical.patient')
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.spell_pool = cls.registry('nh.clinical.spell')
        # DEVICES DATA MODELS
        cls.device_pool = cls.registry('nh.clinical.device')
        cls.type_pool = cls.registry('nh.clinical.device.type')
        cls.category_pool = cls.registry('nh.clinical.device.category')
        cls.session_pool = cls.registry('nh.clinical.device.session')
        cls.connect_pool = cls.registry('nh.clinical.device.connect')
        cls.disconnect_pool = cls.registry('nh.clinical.device.disconnect')

        cls.wm_group_id = cls.groups_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Shift Coordinator Group']])[0]
        cls.admin_group_id = cls.groups_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Admin Group']])

        cls.hospital_id = cls.location_pool.create(
            cr, uid, {'name': 'Test Hospital', 'code': 'TESTHOSP',
                      'usage': 'hospital'})
        cls.pos_id = cls.pos_pool.create(
            cr, uid, {'name': 'Test POS', 'location_id': cls.hospital_id})

        cls.adt_uid = cls.user_pool.create(
            cr, uid, {'name': 'Admin 0', 'login': 'user_000',
                      'password': 'user_000',
                      'groups_id': [[4, cls.admin_group_id[0]]],
                      'pos_id': cls.pos_id})

        cls.ward_id = cls.location_pool.create(
            cr, uid, {'name': 'Ward0', 'code': 'W0', 'usage': 'ward',
                      'parent_id': cls.hospital_id, 'type': 'poc'})
        cls.bed_id = cls.location_pool.create(
            cr, uid, {'name': 'Bed0', 'code': 'B0', 'usage': 'bed',
                      'parent_id': cls.ward_id, 'type': 'poc'})
        cls.wm_uid = cls.user_pool.create(
            cr, uid, {'name': 'WM0', 'login': 'wm0', 'password': 'wm0',
                      'groups_id': [[4, cls.wm_group_id]],
                      'location_ids': [[5]]})

        cls.patients = [
            cls.patient_pool.create(cr, uid, {
                'other_identifier': 'TESTP000'+str(i),
                'patient_identifier': 'TESTNHS0'+str(i)}) for i in range(2)
        ]

        cls.activity_pool.start(cr, uid, cls.spell_pool.create_activity(
            cr, uid, {}, {'patient_id': cls.patients[0], 'pos_id': cls.pos_id,
                          'code': 'AD00'}))
        cls.type_ids = cls.type_pool.search(cr, uid, [])
        cls.device_id = cls.device_pool.create(
            cr, uid, {'type_id': cls.type_ids[0], 'serial_number': '000001'})

    def test_01_device_session(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Get session activity id when the patient has no session
        self.assertFalse(self.session_pool.get_activity_id(
            cr, uid, self.patients[0], self.type_ids[0]))

        # Scenario 2: Start a device session without providing specific device
        session_data = {
            'device_type_id': self.type_ids[0],
            'location': 'arm',
            'patient_id': self.patients[0]
        }
        session_id = self.session_pool.create_activity(cr, self.wm_uid, {},
                                                       session_data)
        self.activity_pool.start(cr, self.wm_uid, session_id)
        device = self.device_pool.browse(cr, uid, self.device_id)
        self.assertTrue(device.is_available, msg="Device is not available")

        # Scenario 3: Get session activity id when the patient has one session
        self.assertEqual(self.session_pool.get_activity_id(
            cr, uid, self.patients[0], self.type_ids[0]), session_id)

        # Scenario 4: Start a device session providing specific device
        session_data = {
            'device_type_id': self.type_ids[0],
            'device_id': self.device_id,
            'location': 'arm',
            'patient_id': self.patients[0]
        }
        session2_id = self.session_pool.create_activity(cr, self.wm_uid, {},
                                                        session_data)
        self.activity_pool.start(cr, self.wm_uid, session2_id)
        device = self.device_pool.browse(cr, uid, self.device_id)
        self.assertFalse(device.is_available, msg="Device is still available")

        # Scenario 5:
        # Get session activity id when the patient
        # has more than one session started.
        self.assertIn(
            self.session_pool.get_activity_id(cr, uid, self.patients[0],
                                              self.type_ids[0]),
            [session_id, session2_id])

        # Scenario 6:
        # Complete a device session without providing specific device.
        self.activity_pool.complete(cr, self.wm_uid, session_id)
        device = self.device_pool.browse(cr, uid, self.device_id)
        self.assertFalse(device.is_available, msg="Device was made available")

        # Scenario 7: Complete a device session providing specific device
        self.activity_pool.complete(cr, self.wm_uid, session2_id)
        device = self.device_pool.browse(cr, uid, self.device_id)
        self.assertTrue(device.is_available, msg="Device is not available")

    def test_02_device_connect(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Create device connect without providing specific device
        connect_data = {
            'device_type_id': self.type_ids[0],
            'patient_id': self.patients[0]
        }
        connect_id = self.connect_pool.create_activity(cr, self.wm_uid, {},
                                                       connect_data)
        self.assertTrue(connect_id, msg="Connect Activity not generated")
        self.activity_pool.complete(cr, self.wm_uid, connect_id)

        # Scenario 2: Create device connect providing specific device
        connect_data = {
            'device_id': self.device_id,
            'patient_id': self.patients[0]
        }
        connect2_id = self.connect_pool.create_activity(cr, self.wm_uid, {},
                                                        connect_data)
        self.assertTrue(connect2_id, msg="Connect Activity not generated")
        connect = self.activity_pool.browse(cr, uid, connect2_id)
        self.assertEqual(connect.data_ref.device_type_id.id, self.type_ids[0],
                         msg="Device type does not match")
        self.activity_pool.complete(cr, self.wm_uid, connect2_id)

        # Scenario 3: Create device connect without patient
        connect_data = {
            'device_id': self.device_id
        }
        with self.assertRaises(except_orm):
            self.connect_pool.create_activity(cr, self.wm_uid, {},
                                              connect_data)

        # Scenario 4: Create device connect without device information
        connect_data = {
            'patient_id': self.patients[0]
        }
        with self.assertRaises(except_orm):
            self.connect_pool.create_activity(cr, self.wm_uid, {},
                                              connect_data)

        # Scenario 5: Attempt to connect a device to a not admitted patient
        connect_data = {
            'device_type_id': self.type_ids[0],
            'patient_id': self.patients[1]
        }
        with self.assertRaises(except_orm):
            self.connect_pool.create_activity(cr, self.wm_uid, {},
                                              connect_data)

        # Scenario 6: Attempt to connect an already used device to a patient
        connect_data = {
            'device_id': self.device_id,
            'patient_id': self.patients[0]
        }
        with self.assertRaises(except_orm):
            self.connect_pool.create_activity(cr, self.wm_uid, {},
                                              connect_data)

    def test_03_device_disconnect(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Create device disconnect providing specific device
        disconnect_data = {
            'device_id': self.device_id,
            'patient_id': self.patients[0]
        }
        disconnect_id = self.disconnect_pool.create_activity(
            cr, self.wm_uid, {}, disconnect_data)
        self.assertTrue(disconnect_id, msg="Disconnect Activity not generated")
        disconnect = self.activity_pool.browse(cr, uid, disconnect_id)
        self.assertEqual(disconnect.data_ref.device_type_id.id,
                         self.type_ids[0], msg="Device type does not match")
        self.activity_pool.complete(cr, self.wm_uid, disconnect_id)

        # Scenario 2:
        # Create device disconnect without providing specific device.
        disconnect_data = {
            'device_type_id': self.type_ids[0],
            'patient_id': self.patients[0]
        }
        disconnect_id = self.disconnect_pool.create_activity(
            cr, self.wm_uid, {}, disconnect_data)
        self.assertTrue(disconnect_id, msg="Disconnect Activity not generated")
        self.activity_pool.complete(cr, self.wm_uid, disconnect_id)

        # Scenario 3: Create device disconnect without patient
        disconnect_data = {
            'device_id': self.device_id
        }
        with self.assertRaises(except_orm):
            self.disconnect_pool.create_activity(cr, self.wm_uid, {},
                                                 disconnect_data)

        # Scenario 4: Create device disconnect without device information
        disconnect_data = {
            'patient_id': self.patients[0]
        }
        with self.assertRaises(except_orm):
            self.disconnect_pool.create_activity(cr, self.wm_uid, {},
                                                 disconnect_data)

        # Scenario 5:
        # Attempt to disconnect a device not connected to the patient.
        disconnect_data = {
            'device_id': self.device_id,
            'patient_id': self.patients[0]
        }
        with self.assertRaises(except_orm):
            self.disconnect_pool.create_activity(cr, self.wm_uid, {},
                                                 disconnect_data)

        # Scenario 6:
        # Attempt to disconnect a device not connected to the patient (type).
        disconnect_data = {
            'device_type_id': self.type_ids[0],
            'patient_id': self.patients[0]
        }
        with self.assertRaises(except_orm):
            self.disconnect_pool.create_activity(cr, self.wm_uid, {},
                                                 disconnect_data)

    def test_04_device_name_get(self):
        cr, uid = self.cr, self.uid

        type = self.type_pool.browse(cr, uid, self.type_ids[0])
        res = self.device_pool.name_get(cr, uid, [self.device_id])
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][1], type.name+'/000001')
