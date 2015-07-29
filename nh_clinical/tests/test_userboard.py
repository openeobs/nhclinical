from openerp.tests import common
from openerp.osv.orm import except_orm


class TestUserboard(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestUserboard, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.users_pool = cls.registry('res.users')
        cls.groups_pool = cls.registry('res.groups')
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

        cls.admin_group_id = cls.groups_pool.search(cr, uid, [['name', '=', 'NH Clinical Admin Group']])

        cls.hospital_id = cls.location_pool.create(cr, uid, {'name': 'Test Hospital', 'code': 'TESTHOSP',
                                                             'usage': 'hospital'})
        cls.pos_id = cls.pos_pool.create(cr, uid, {'name': 'Test POS', 'location_id': cls.hospital_id})

        cls.adt_uid = cls.users_pool.create(cr, uid, {'name': 'Admin 0', 'login': 'user_000',
                                                        'password': 'user_000',
                                                        'groups_id': [[4, cls.admin_group_id[0]]],
                                                        'pos_id': cls.pos_id})

    def test_00_change_password_get_default_user_ids(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Use context
        res = self.passwiz_pool._default_user_ids(cr, uid, context={'active_ids': self.adt_uid})
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res[0]), 3)
        self.assertDictEqual(res[0][2], {'user_id': self.adt_uid, 'user_login': 'user_000'})

        # Scenario 2: Use no context
        res = self.passwiz_pool._default_user_ids(cr, uid, context=None)
        self.assertEqual(len(res), 0)