from openerp.tests.common import SingleTransactionCase
from datetime import datetime as dt, timedelta as td
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf


class TestCoreAPI(SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestCoreAPI, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.users_pool = cls.registry('res.users')
        cls.groups_pool = cls.registry('res.groups')
        cls.partner_pool = cls.registry('res.partner')
        cls.activity_pool = cls.registry('nh.activity')
        cls.patient_pool = cls.registry('nh.clinical.patient')
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.api = cls.registry('nh.clinical.api')

        cls.wm_group_id = cls.groups_pool.search(cr, uid, [['name', '=', 'NH Clinical Ward Manager Group']])
        cls.nurse_group_id = cls.groups_pool.search(cr, uid, [['name', '=', 'NH Clinical Nurse Group']])
        cls.hca_group_id = cls.groups_pool.search(cr, uid, [['name', '=', 'NH Clinical HCA Group']])
        cls.doctor_group_id = cls.groups_pool.search(cr, uid, [['name', '=', 'NH Clinical Doctor Group']])
        cls.admin_group_id = cls.groups_pool.search(cr, uid, [['name', '=', 'NH Clinical Admin Group']])

        cls.hospital_id = cls.location_pool.create(cr, uid, {'name': 'Test Hospital', 'code': 'TESTHOSP',
                                                             'usage': 'hospital'})
        cls.pos_id = cls.pos_pool.create(cr, uid, {'name': 'Test POS', 'location_id': cls.hospital_id})

        cls.adt_uid = cls.users_pool.create(cr, uid, {'name': 'Admin 0', 'login': 'user_000',
                                                        'password': 'user_000',
                                                        'groups_id': [[4, cls.admin_group_id[0]]],
                                                        'pos_id': cls.pos_id})

        cls.locations = {}
        for i in range(3):
            wid = cls.location_pool.create(cr, uid, {'name': 'Ward'+str(i), 'code': 'WARD'+str(i), 'usage': 'ward',
                                                     'parent_id': cls.hospital_id, 'type': 'poc'})
            cls.locations[wid] = [cls.location_pool.create(cr, uid, {'name': 'Bed'+str(i)+str(j),
                                                                     'code': 'BED'+str(i)+str(j),
                                                                     'usage': 'bed', 'parent_id': wid,
                                                                     'type': 'poc'}) for j in range(3)]

    def test_01_register(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Register a patient with Hospital Number
        patient_data = {
            'family_name': "Fname",
            'given_name': 'Gname',
            'dob': '1988-08-14 18:00:00',
            'gender': 'M',
            'sex': 'M'
        }

        self.api.register(cr, self.adt_uid, 'TESTP0001', patient_data)

        patient_id = self.patient_pool.search(cr, uid, [('other_identifier', '=', 'TESTP0001')])
        self.assertTrue(patient_id, msg="Patient was not created")
        register_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.adt.patient.register'], ['patient_id', '=', patient_id[0]]])
        self.assertTrue(register_id, msg="Register Activity not generated")
        activity = self.activity_pool.browse(cr, uid, register_id[0])
        self.assertEqual(activity.state, 'completed')

        # Scenario 2: Register a patient with NHS Number
        patient_data = {
            'patient_identifier': 'TESTNHS001',
            'family_name': "Fname2",
            'given_name': 'Gname2',
            'gender': 'F',
            'sex': 'F'
        }

        self.api.register(cr, self.adt_uid, '', patient_data)

        patient_id = self.patient_pool.search(cr, uid, [('patient_identifier', '=', 'TESTNHS001')])
        self.assertTrue(patient_id, msg="Patient was not created")
        register_id = self.activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.adt.patient.register'], ['patient_id', '=', patient_id[0]]])
        self.assertTrue(register_id, msg="Register Activity not generated")
        activity = self.activity_pool.browse(cr, uid, register_id[0])
        self.assertEqual(activity.state, 'completed')