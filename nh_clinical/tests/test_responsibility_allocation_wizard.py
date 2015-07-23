__author__ = 'Will'

from openerp.tests.common import TransactionCase


class TestResponsibilityAllocationWizard(TransactionCase):

    def setUp(self):
        super(TestResponsibilityAllocationWizard, self).setUp()

        self.user_pool = self.registry('res.users')
        self.wizard_pool = self.registry('nh.clinical.responsibility.allocation')

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








