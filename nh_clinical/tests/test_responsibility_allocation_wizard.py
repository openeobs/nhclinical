__author__ = 'Will'

from openerp.tests.common import SingleTransactionCase


class TestResponsibilityAllocationWizard(SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestResponsibilityAllocationWizard, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.users_pool = cls.registry('res.users')
        cls.wizard_pool = cls.registry('nh.clinical.responsibility.allocation')
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.groups_pool = cls.registry('res.groups')

        cls.admin_group_id = cls.groups_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Admin Group']]
        )
        cls.hospital_id = cls.location_pool.create(
            cr, uid, {'name': 'Test Hospital', 'code': 'TESTHOSP',
                      'usage': 'hospital'}
        )
        cls.pos_id = cls.pos_pool.create(
            cr, uid, {'name': 'Test POS', 'location_id': cls.hospital_id}
        )
        cls.adt_uid = cls.users_pool.create(
            cr, uid, {'name': 'Admin 0', 'login': 'user_000',
                      'password': 'user_000',
                      'groups_id': [[4, cls.admin_group_id[0]]],
                      'pos_id': cls.pos_id}
        )

    def test_01_onchange_user_id_returns_empty_dict_when_no_user_id(self):
        cr, uid = self.cr, self.uid
        user_ids = [False, None, '']

        for user_id in user_ids:
            result = self.wizard_pool.onchange_user_id(cr, uid, None, user_id, context=None)
            self.assertEquals(result, {})

    def test_02_onchange_clear_removes_location_when_clear_is_True(self):
        cr, uid = self.cr, self.uid

        result = self.wizard_pool.onchange_clear(cr, uid, None, True, context=None)
        self.assertEquals(result['value']['clear_locations'], False)

    def test_03_onchange_clear_does_not_append_clear_location_when_clear_is_False(self):
        cr, uid = self.cr, self.uid
        clears = [False, None, '']

        for clear in clears:
            result = self.wizard_pool.onchange_clear(cr, uid, None, clear, context=None)
            self.assertEquals(result, {'value': {'location_ids': [[6, False, []]]}})









