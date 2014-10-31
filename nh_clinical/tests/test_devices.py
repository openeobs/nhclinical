from openerp.tests import common
from datetime import datetime as dt
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

import logging
_logger = logging.getLogger(__name__)

from faker import Faker
fake = Faker()
seed = fake.random_int(min=0, max=9999999)


def next_seed():
    global seed
    seed += 1
    return seed


class TestDevices(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestDevices, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.users_pool = cls.registry('res.users')
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

        cls.apidemo = cls.registry('nh.clinical.api.demo')

        cls.patient_ids = cls.apidemo.build_unit_test_env(cr, uid, bed_count=4, patient_count=4)

        cls.wu_id = cls.location_pool.search(cr, uid, [('code', '=', 'U')])[0]
        cls.wt_id = cls.location_pool.search(cr, uid, [('code', '=', 'T')])[0]
        cls.pos_id = cls.location_pool.read(cr, uid, cls.wu_id, ['pos_id'])['pos_id'][0]
        cls.pos_location_id = cls.pos_pool.read(cr, uid, cls.pos_id, ['location_id'])['location_id'][0]

        cls.wmu_id = cls.users_pool.search(cr, uid, [('login', '=', 'WMU')])[0]
        cls.wmt_id = cls.users_pool.search(cr, uid, [('login', '=', 'WMT')])[0]
        cls.nu_id = cls.users_pool.search(cr, uid, [('login', '=', 'NU')])[0]
        cls.nt_id = cls.users_pool.search(cr, uid, [('login', '=', 'NT')])[0]
        cls.adt_id = cls.users_pool.search(cr, uid, [('groups_id.name', 'in', ['NH Clinical ADT Group']), ('pos_id', '=', cls.pos_id)])[0]

    def test_device_Connect_Session_and_Disconnect(self):
        cr, uid = self.cr, self.uid

        patient_id = fake.random_element(self.patient_ids)
        code = str(fake.random_int(min=1000001, max=9999999))
        spell_data = {
            'patient_id': patient_id,
            'pos_id': self.pos_id,
            'code': code,
            'start_date': dt.now().strftime(DTF)}
        spell_activity_id = self.spell_pool.create_activity(cr, uid, {}, spell_data)
        self.activity_pool.start(cr, uid, spell_activity_id)
        
        device_type_ids = self.type_pool.search(cr, uid, [])
        type_id = fake.random_element(device_type_ids)
        type2_id = fake.random_element(device_type_ids)
        while type_id == type2_id:
            type2_id = fake.random_element(device_type_ids)
        device_data = {
            'type_id': type_id,
            'serial_number': str(fake.random_int(min=1000001, max=9999999))
        }
        device_id = self.device_pool.create(cr, uid, device_data)
        
        # Device Connect 1
        connect_data = {
            'patient_id': patient_id,
            'device_id': device_id
        }
        connect_activity_id = self.connect_pool.create_activity(cr, uid, {}, {})
        self.activity_pool.submit(cr, self.wmu_id, connect_activity_id, connect_data)
        check_connect = self.activity_pool.browse(cr, uid, connect_activity_id)
        
        # test device connect activity submitted data
        self.assertTrue(check_connect.data_ref.patient_id.id == patient_id, msg="Device Connect: Patient id was not submitted correctly")
        self.assertTrue(check_connect.data_ref.device_id.id == device_id, msg="Device Connect: Device id was not submitted correctly")
        self.assertTrue(check_connect.data_ref.device_type_id.id == type_id, msg="Device Connect: Type id was not registered correctly")
        
        # Complete Device Connect
        self.activity_pool.complete(cr, self.wmu_id, connect_activity_id)
        check_connect = self.activity_pool.browse(cr, uid, connect_activity_id)
        self.assertTrue(check_connect.state == 'completed', msg="Device Connect not completed successfully")
        self.assertTrue(check_connect.date_terminated, msg="Device Connect Completed: Date terminated not registered")
        session_ids = self.session_pool.search(cr, uid, [['patient_id', '=', patient_id], ['device_id', '=', device_id]])
        self.assertTrue(session_ids, msg="Device Connect Completed: Device session not created")
        device_session_id = session_ids[0]
        check_session = self.session_pool.browse(cr, uid, device_session_id)
        self.assertTrue(check_session.activity_id.state == 'started', msg="Device Connect Completed: Device session not started")
        check_device = self.device_pool.browse(cr, uid, device_id)
        self.assertFalse(check_device.is_available, msg="Device Connect Completed: Device availability not updated")

        # Device Connect 2
        connect_data = {
            'patient_id': patient_id,
            'device_type_id': type2_id
        }
        connect_activity_id = self.connect_pool.create_activity(cr, uid, {}, {})
        self.activity_pool.submit(cr, self.wmu_id, connect_activity_id, connect_data)
        check_connect = self.activity_pool.browse(cr, uid, connect_activity_id)

        # test device connect activity submitted data
        self.assertTrue(check_connect.data_ref.patient_id.id == patient_id, msg="Device Connect: Patient id was not submitted correctly")
        self.assertFalse(check_connect.data_ref.device_id, msg="Device Connect: Device id was not submitted correctly")
        self.assertTrue(check_connect.data_ref.device_type_id.id == type2_id, msg="Device Connect: Type id was not submitted correctly")

        # Complete Device Connect
        self.activity_pool.complete(cr, self.wmu_id, connect_activity_id)
        check_connect = self.activity_pool.browse(cr, uid, connect_activity_id)
        self.assertTrue(check_connect.state == 'completed', msg="Device Connect not completed successfully")
        self.assertTrue(check_connect.date_terminated, msg="Device Connect Completed: Date terminated not registered")
        session_ids = self.session_pool.search(cr, uid, [['patient_id', '=', patient_id], ['device_type_id', '=', type2_id]])
        self.assertTrue(session_ids, msg="Device Connect Completed: Device session not created")
        device_session2_id = session_ids[0]
        check_session = self.session_pool.browse(cr, uid, device_session2_id)
        self.assertTrue(check_session.activity_id.state == 'started', msg="Device Connect Completed: Device session not started")
        
        # Device Disconnect 1
        disconnect_data = {
            'patient_id': patient_id,
            'device_id': device_id
        }
        disconnect_activity_id = self.disconnect_pool.create_activity(cr, uid, {}, {})
        self.activity_pool.submit(cr, self.wmu_id, disconnect_activity_id, disconnect_data)
        check_disconnect = self.activity_pool.browse(cr, uid, disconnect_activity_id)
        
        # test device disconnect activity submitted data
        self.assertTrue(check_disconnect.data_ref.patient_id.id == patient_id, msg="Device disconnect: Patient id was not submitted correctly")
        self.assertTrue(check_disconnect.data_ref.device_id.id == device_id, msg="Device disconnect: Device id was not submitted correctly")
        self.assertTrue(check_disconnect.data_ref.device_type_id.id == type_id, msg="Device disconnect: Type id was not registered correctly")
        
        # Complete Device Disconnect
        self.activity_pool.complete(cr, self.wmu_id, disconnect_activity_id)
        check_disconnect = self.activity_pool.browse(cr, uid, disconnect_activity_id)
        self.assertTrue(check_disconnect.state == 'completed', msg="Device disconnect not completed successfully")
        self.assertTrue(check_disconnect.date_terminated, msg="Device disconnect Completed: Date terminated not registered")
        check_session = self.session_pool.browse(cr, uid, device_session_id)
        self.assertTrue(check_session.activity_id.state == 'completed', msg="Device disconnect Completed: Device session not completed")
        check_device = self.device_pool.browse(cr, uid, device_id)
        self.assertTrue(check_device.is_available, msg="Device disconnect Completed: Device availability not updated")
        
        # Device Disconnect 2
        disconnect_data = {
            'patient_id': patient_id,
            'device_type_id': type2_id
        }
        disconnect_activity_id = self.disconnect_pool.create_activity(cr, uid, {}, {})
        self.activity_pool.submit(cr, self.wmu_id, disconnect_activity_id, disconnect_data)
        check_disconnect = self.activity_pool.browse(cr, uid, disconnect_activity_id)

        # test device disconnect activity submitted data
        self.assertTrue(check_disconnect.data_ref.patient_id.id == patient_id, msg="Device disconnect: Patient id was not submitted correctly")
        self.assertFalse(check_disconnect.data_ref.device_id, msg="Device disconnect: Device id was not submitted correctly")
        self.assertTrue(check_disconnect.data_ref.device_type_id.id == type2_id, msg="Device disconnect: Type id was not submitted correctly")

        # Complete Device Disconnect
        self.activity_pool.complete(cr, self.wmu_id, disconnect_activity_id)
        check_disconnect = self.activity_pool.browse(cr, uid, disconnect_activity_id)
        self.assertTrue(check_disconnect.state == 'completed', msg="Device disconnect not completed successfully")
        self.assertTrue(check_disconnect.date_terminated, msg="Device disconnect Completed: Date terminated not registered")
        check_session = self.session_pool.browse(cr, uid, device_session2_id)
        self.assertTrue(check_session.activity_id.state == 'completed', msg="Device disconnect Completed: Device session not completed")