from openerp.tests import common
from openerp.osv.orm import except_orm

import logging

_logger = logging.getLogger(__name__)


class TestBaseExtension(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestBaseExtension, cls).setUpClass()
        cr, uid = cls.cr, cls.uid
        cls.title_pool = cls.registry('res.partner.title')
        cls.category_pool = cls.registry('res.partner.category')
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.user_pool = cls.registry('res.users')
        cls.group_pool = cls.registry('res.groups')

        cls.wm_role_id = cls.category_pool.search(cr, uid, [['name', '=', 'Ward Manager']])[0]
        cls.nurse_role_id = cls.category_pool.search(cr, uid, [['name', '=', 'Nurse']])[0]
        cls.hca_role_id = cls.category_pool.search(cr, uid, [['name', '=', 'HCA']])[0]

    def test_01_get_title_by_name(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Get new title with create flag ON.
        title_id = self.title_pool.get_title_by_name(cr, uid, 'Mr.')
        self.assertTrue(title_id, msg="Title creation failed")
        title = self.title_pool.browse(cr, uid, title_id)
        self.assertEqual(title.name, 'mr', msg="Title not formated")

        # Scenario 2: Get the same title with different formats
        self.assertEqual(title_id, self.title_pool.get_title_by_name(cr, uid, 'Mr'))
        self.assertEqual(title_id, self.title_pool.get_title_by_name(cr, uid, 'MR'))
        self.assertEqual(title_id, self.title_pool.get_title_by_name(cr, uid, 'MR.'))
        self.assertEqual(title_id, self.title_pool.get_title_by_name(cr, uid, 'Mr '))
        self.assertEqual(title_id, self.title_pool.get_title_by_name(cr, uid, ' M R '))
        self.assertEqual(title_id, self.title_pool.get_title_by_name(cr, uid, 'MR . '))

        # Scenario 3: Get new title with create flag OFF.
        self.assertFalse(self.title_pool.get_title_by_name(cr, uid, 'Dr', create=False), msg="Unexpected id returned")

    def test_02_check_pos(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Check user has no Point of Service
        self.assertFalse(self.user_pool.check_pos(cr, uid, uid))

        # Create POS and a User assigned to it
        location_id = self.location_pool.create(cr, uid, {'name': 'Test Loc', 'code': 'TESTLOC01'})
        pos_id = self.pos_pool.create(cr, uid, {'name': 'Test POS', 'location_id': location_id})
        user_id = self.user_pool.create(cr, uid, {'name': 'Test User', 'login': 'testuser', 'pos_id': pos_id})

        # Scenario 2: Check user has Point of Service
        self.assertTrue(self.user_pool.check_pos(cr, uid, user_id))

        # Scenario 3: Check exception is raised if there is no PoS and exception flag is ON.
        with self.assertRaises(except_orm):
            self.user_pool.check_pos(cr, uid, uid, exception=True)

    def test_03_category_name_get(self):
        cr, uid = self.cr, self.uid

        res = self.category_pool.name_get(cr, uid, [self.wm_role_id])
        self.assertListEqual(res, [(self.wm_role_id, 'Ward Manager')])
        res = self.category_pool.name_get(cr, uid, [self.hca_role_id], {'tz': 'Europe/London'})
        self.assertListEqual(res, [(self.hca_role_id, 'HCA')])

    def test_04_category_get_child_of_ids(self):
        cr, uid = self.cr, self.uid

        child_ids = self.category_pool.get_child_of_ids(cr, uid, self.hca_role_id)
        self.assertListEqual(child_ids, [self.hca_role_id])
        child_ids = self.category_pool.get_child_of_ids(cr, uid, self.nurse_role_id)
        self.assertListEqual(child_ids, [self.nurse_role_id, self.hca_role_id])
        child_ids = self.category_pool.get_child_of_ids(cr, uid, self.wm_role_id)
        self.assertListEqual(child_ids, [self.wm_role_id, self.nurse_role_id, self.hca_role_id])
