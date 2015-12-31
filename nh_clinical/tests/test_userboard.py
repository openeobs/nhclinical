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
        cls.category_pool = cls.registry('res.partner.category')
        cls.activity_pool = cls.registry('nh.activity')
        cls.patient_pool = cls.registry('nh.clinical.patient')
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.spell_pool = cls.registry('nh.clinical.spell')
        # USERBOARD MODELS
        cls.passwiz_pool = cls.registry('change.password.wizard')
        cls.uman_pool = cls.registry('nh.clinical.user.management')

        cls.admin_group_id = cls.group_pool.search(cr, uid, [['name', '=', 'NH Clinical Admin Group']])
        cls.hca_group_id = cls.group_pool.search(cr, uid, [['name', '=', 'NH Clinical HCA Group']])[0]
        cls.nurse_group_id = cls.group_pool.search(cr, uid, [['name', '=', 'NH Clinical Nurse Group']])[0]
        cls.wm_group_id = cls.group_pool.search(cr, uid, [['name', '=', 'NH Clinical Ward Manager Group']])[0]
        cls.sm_group_id = cls.group_pool.search(cr, uid, [['name', '=', 'NH Clinical Senior Manager Group']])[0]
        cls.dr_group_id = cls.group_pool.search(cr, uid, [['name', '=', 'NH Clinical Doctor Group']])[0]

        cls.admin_role_id = cls.category_pool.search(cr, uid, [['name', '=', 'System Administrator']])[0]
        cls.wm_role_id = cls.category_pool.search(cr, uid, [['name', '=', 'Ward Manager']])[0]
        cls.nurse_role_id = cls.category_pool.search(cr, uid, [['name', '=', 'Nurse']])[0]
        cls.hca_role_id = cls.category_pool.search(cr, uid, [['name', '=', 'HCA']])[0]

        cls.hospital_id = cls.location_pool.create(cr, uid, {'name': 'Test Hospital', 'code': 'TESTHOSP',
                                                             'usage': 'hospital'})
        cls.pos_id = cls.pos_pool.create(cr, uid, {'name': 'Test POS', 'location_id': cls.hospital_id})

        cls.adt_uid = cls.user_pool.create(cr, uid, {'name': 'Admin 0', 'login': 'user_000',
                                                        'password': 'user_000',
                                                        'groups_id': [[4, cls.admin_group_id[0]]],
                                                        'category_id': [[4, cls.admin_role_id]],
                                                        'pos_id': cls.pos_id})
        cls.ward_id = cls.location_pool.create(cr, uid, {
            'name': 'Ward0', 'code': 'W0', 'usage': 'ward', 'parent_id': cls.hospital_id, 'type': 'poc'
        })
        cls.bed_id = cls.location_pool.create(cr, uid, {
            'name': 'Bed0', 'code': 'B0', 'usage': 'bed', 'parent_id': cls.ward_id, 'type': 'poc'
        })
        cls.hca_uid = cls.user_pool.create(cr, uid, {
            'name': 'HCA0', 'login': 'hca0', 'password': 'hca0', 'groups_id': [[4, cls.hca_group_id]],
            'location_ids': [[5]]
        })
        cls.nurse_uid = cls.user_pool.create(cr, uid, {
            'name': 'NURSE0', 'login': 'n0', 'password': 'n0', 'groups_id': [[4, cls.nurse_group_id]],
            'location_ids': [[5]]
        })
        cls.wm_uid = cls.user_pool.create(cr, uid, {
            'name': 'WM0', 'login': 'wm0', 'password': 'wm0', 'groups_id': [[4, cls.wm_group_id]],
            'location_ids': [[5]], 'category_id': [[4, cls.wm_role_id]]
        })
        cls.sm_uid = cls.user_pool.create(cr, uid, {
            'name': 'SM0', 'login': 'sm0', 'password': 'sm0', 'groups_id': [[4, cls.sm_group_id]],
            'location_ids': [[5]]
        })
        cls.dr_uid = cls.user_pool.create(cr, uid, {
            'name': 'DR0', 'login': 'dr0', 'password': 'dr0', 'groups_id': [[4, cls.dr_group_id]],
            'location_ids': [[5]]
        })

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

    def test_02_user_management_create(self):
        cr, uid = self.cr, self.uid

        user_data = {
            'name': 'HCA2', 'login': 'hca2', 'category_id': [[4, self.hca_role_id]]
        }
        hca_uid = self.uman_pool.create(cr, self.wm_uid, user_data)
        self.assertTrue(hca_uid, msg="HCA user not created")
        user = self.user_pool.browse(cr, uid, hca_uid)
        self.assertEqual(user.name, 'HCA2')
        self.assertEqual(user.login, 'hca2')
        groups = [g.name for g in user.groups_id]
        self.assertTrue('NH Clinical HCA Group' in groups, msg="User created without HCA group")
        self.assertTrue('Employee' in groups, msg="User created without Employee group")

    def test_03_user_management_write(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Update HCA user with Ward Manager user
        user_id = self.uman_pool.search(cr, uid, [['name', '=', 'HCA2']])
        user_data = {
            'name': 'TU2', 'login': 'tu2', 'category_id': [[6, 0, [self.nurse_role_id]]]
        }
        self.assertTrue(self.uman_pool.write(cr, self.wm_uid, user_id, user_data))
        user = self.user_pool.browse(cr, uid, user_id)
        self.assertEqual(user.name, 'TU2')
        self.assertEqual(user.login, 'tu2')
        groups = [g.name for g in user.groups_id]
        self.assertFalse('NH Clinical HCA Group' in groups, msg="HCA group not removed")
        self.assertTrue('NH Clinical Nurse Group' in groups, msg="Nurse group missing")
        self.assertTrue('Employee' in groups, msg="Employee group removed")

        # Scenario 2: Update Admin user with HCA user
        user_data = {
            'name': 'TU3', 'login': 'tu3', 'category_id': [[6, 0, [self.nurse_role_id]]]
        }
        with self.assertRaises(except_orm):
            self.uman_pool.write(cr, user_id[0], self.adt_uid, user_data)

    def test_04_user_management_allocate_responsibility(self):
        cr, uid = self.cr, self.uid

        user_id = self.uman_pool.search(cr, uid, [['name', '=', 'TU2']])
        res = self.uman_pool.allocate_responsibility(cr, self.wm_uid, user_id, context={})
        self.assertDictEqual(res, {
            'type': 'ir.actions.act_window', 'res_model': 'nh.clinical.responsibility.allocation',
            'name': 'Location Responsibility Allocation', 'view_mode': 'form', 'view_type': 'tree,form',
            'target': 'new', 'context': {'default_user_id': user_id[0]}
        })

    def test_05_user_management_deactivate(self):
        cr, uid = self.cr, self.uid
        user_id = self.uman_pool.search(cr, uid, [['name', '=', 'TU2']])

        # Scenario 1: Deactivate a user
        self.assertTrue(self.uman_pool.deactivate(cr, self.adt_uid, user_id))
        user = self.user_pool.browse(cr, uid, user_id[0])
        self.assertFalse(user.active, msg="User not deactivated")

        # Scenario 2: Attempt to deactivate yourself
        with self.assertRaises(except_orm):
            self.uman_pool.deactivate(cr, self.adt_uid, [self.adt_uid])

    def test_06_user_management_activate(self):
        cr, uid = self.cr, self.uid
        user_id = self.uman_pool.search(cr, uid, [['active', '=', False]], order='id desc')

        self.assertTrue(self.uman_pool.activate(cr, self.adt_uid, user_id[0]))
        user = self.user_pool.browse(cr, uid, user_id[0])
        self.assertTrue(user.active, msg="User not activated")

    def test_07_user_management_fields_view_get(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: fields_view_get tree view
        self.assertTrue(self.uman_pool.fields_view_get(cr, uid, view_id=None, view_type='tree', context={}))

        # Scenario 2: fields_view_get form view
        res = self.uman_pool.fields_view_get(cr, self.wm_uid, context={})
        self.assertTrue(res)
        self.assertListEqual(res['fields']['category_id']['domain'],
                             [['id', 'in', [self.wm_role_id, self.nurse_role_id, self.hca_role_id]]])