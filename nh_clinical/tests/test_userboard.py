from openerp.tests import common
from openerp.osv.orm import except_orm


class TestUserboard(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestUserboard, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.user_pool = cls.registry('res.users')
        cls.group_pool = cls.registry('res.groups')
        cls.partner_pool = cls.registry('res.partner')
        cls.activity_pool = cls.registry('nh.activity')
        cls.patient_pool = cls.registry('nh.clinical.patient')
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.spell_pool = cls.registry('nh.clinical.spell')
        # USERBOARD MODELS
        cls.passwiz_pool = cls.registry('change.password.wizard')
        cls.userboard_pool = cls.registry('nh.clinical.userboard')
        cls.adminboard_pool = cls.registry('nh.clinical.admin.userboard')

        cls.admin_group_id = cls.group_pool.search(cr, uid, [['name', '=', 'NH Clinical Admin Group']])
        cls.hca_group_id = cls.group_pool.search(cr, uid, [['name', '=', 'NH Clinical HCA Group']])[0]
        cls.nurse_group_id = cls.group_pool.search(cr, uid, [['name', '=', 'NH Clinical Nurse Group']])[0]
        cls.wm_group_id = cls.group_pool.search(cr, uid, [['name', '=', 'NH Clinical Ward Manager Group']])[0]
        cls.sm_group_id = cls.group_pool.search(cr, uid, [['name', '=', 'NH Clinical Senior Manager Group']])[0]
        cls.dr_group_id = cls.group_pool.search(cr, uid, [['name', '=', 'NH Clinical Doctor Group']])[0]

        cls.hospital_id = cls.location_pool.create(cr, uid, {'name': 'Test Hospital', 'code': 'TESTHOSP',
                                                             'usage': 'hospital'})
        cls.pos_id = cls.pos_pool.create(cr, uid, {'name': 'Test POS', 'location_id': cls.hospital_id})

        cls.adt_uid = cls.user_pool.create(cr, uid, {'name': 'Admin 0', 'login': 'user_000',
                                                        'password': 'user_000',
                                                        'groups_id': [[4, cls.admin_group_id[0]]],
                                                        'pos_id': cls.pos_id})
        cls.ward_id = cls.location_pool.create(cr, uid, {
            'name': 'Ward0', 'code': 'W0', 'usage': 'ward', 'parent_id': cls.hospital_id, 'type': 'poc'
        })
        cls.bed_id = cls.location_pool.create(cr, uid, {
            'name': 'Bed0', 'code': 'B0', 'usage': 'bed', 'parent_id': cls.ward_id, 'type': 'poc'
        })
        cls.hca_uid = False
        cls.nurse_uid = False
        cls.wm_uid = cls.user_pool.create(cr, uid, {
            'name': 'WM0', 'login': 'wm0', 'password': 'wm0', 'groups_id': [[4, cls.wm_group_id]],
            'location_ids': [[5]]
        })
        cls.sm_uid = False
        cls.dr_uid = False

    def test_01_change_password_get_default_user_ids(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Use context
        res = self.passwiz_pool._default_user_ids(cr, uid, context={'active_ids': self.adt_uid})
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res[0]), 3)
        self.assertDictEqual(res[0][2], {'user_id': self.adt_uid, 'user_login': 'user_000'})

        # Scenario 2: Use no context
        res = self.passwiz_pool._default_user_ids(cr, uid, context=None)
        self.assertEqual(len(res), 0)

    def test_02_userboard_create(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Create new HCA user using userboard
        user_data = {
            'name': 'HCA0', 'login': 'hca0', 'hca': True
        }
        self.hca_uid = self.userboard_pool.create(cr, self.wm_uid, user_data, context={})
        self.assertTrue(self.hca_uid, msg="HCA user not created")
        user = self.user_pool.browse(cr, uid, self.hca_uid)
        self.assertEqual(user.name, 'HCA0')
        self.assertEqual(user.login, 'hca0')
        groups = [g.name for g in user.groups_id]
        self.assertTrue('NH Clinical HCA Group' in groups, msg="User created without HCA group")
        self.assertTrue('Employee' in groups, msg="User created without Employee group")

        # Scenario 2: Create new Senior Manager user using userboard
        user_data = {
            'name': 'SM0', 'login': 'sm0', 'senior_manager': True
        }
        self.sm_uid = self.userboard_pool.create(cr, self.wm_uid, user_data, context=None)
        self.assertTrue(self.sm_uid, msg="Senior Manager user not created")
        user = self.user_pool.browse(cr, uid, self.sm_uid)
        groups = [g.name for g in user.groups_id]
        self.assertTrue('NH Clinical Senior Manager Group' in groups, msg="User created without Senior Manager group")
        self.assertTrue('Employee' in groups, msg="User created without Employee group")
        self.assertTrue('Contact Creation' in groups, msg="User created without Contact Creation group")

        # Scenario 3: Attempt to create a user without any selected role
        user_data = {
            'name': 'X0', 'login': 'x0'
        }
        with self.assertRaises(except_orm):
            self.userboard_pool.create(cr, self.wm_uid, user_data)