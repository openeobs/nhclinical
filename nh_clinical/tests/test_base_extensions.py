from openerp.tests import common

import logging

_logger = logging.getLogger(__name__)


class TestBaseExtension(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestBaseExtension, cls).setUpClass()
        cr, uid = cls.cr, cls.uid
        cls.title_pool = cls.registry('res.partner.title')

    def test_get_title_by_name(self):
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