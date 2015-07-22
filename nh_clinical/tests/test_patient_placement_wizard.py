__author__ = 'Will'
from mock import MagicMock

from openerp.tests.common import TransactionCase


class TestPatientPlacementWizard(TransactionCase):

    def setUp(self):
        super(TestPatientPlacementWizard, self).setUp()

        self.wizard_pool = self.registry('nh.clinical.patient.placement.wizard')
        self.placement_pool = self.registry('nh.clinical.patient.placement')

    def test_01_get_placement_ids_calls_search_with_domain(self):
        cr, uid = self.cr, self.uid
        domain = [('state', 'in', ['draft', 'scheduled', 'started'])]
        self.placement_pool.search = MagicMock()

        self.wizard_pool._get_placement_ids(cr, uid)
        self.placement_pool.search.assert_called_with(
            cr, uid, domain, context=None)
        del self.placement_pool.search

    def test_02_get_placement_ids_returns_list(self):
        cr, uid = self.cr, self.uid

        result = self.wizard_pool._get_placement_ids(cr, uid)
        self.assertTrue(isinstance(result, list))

    def test_03_get_recent_placement_ids_calls_search_with_domain(self):
        cr, uid = self.cr, self.uid
        domain = [('state', 'in', ['completed'])]
        self.placement_pool.search = MagicMock()

        self.wizard_pool._get_recent_placement_ids(cr, uid)
        self.placement_pool.search.assert_called_with(
            cr, uid, domain, limit=3, order='date_terminated desc',
            context=None)
        del self.placement_pool.search

    def test_04_get_recent_placement_ids_returns_list(self):
        cr, uid = self.cr, self.uid

        result = self.wizard_pool._get_recent_placement_ids(cr, uid)
        self.assertTrue(isinstance(result, list))