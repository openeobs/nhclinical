# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
from mock import MagicMock
from openerp.tests.common import TransactionCase


class TestPatientPlacementWizard(TransactionCase):

    def setUp(self):
        super(TestPatientPlacementWizard, self).setUp()

        self.wizard_pool = self.registry(
            'nh.clinical.patient.placement.wizard')
        self.placement_pool = self.registry('nh.clinical.patient.placement')
        self.activity_pool = self.registry('nh.activity')

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

    def test_05_place_patients_calls_start_submit_complete(self):
        cr, uid = self.cr, self.uid
        activity_id = 1
        location_id = 2
        self.activity_pool.start = MagicMock()
        self.activity_pool.submit = MagicMock()
        self.activity_pool.complete = MagicMock()

        result = self.wizard_pool._place_patients(
            cr, uid, activity_id, location_id
        )
        self.activity_pool.start.assert_called_with(
            cr, uid, activity_id, None
        )
        self.activity_pool.submit.assert_called_with(
            cr, uid, activity_id, {'location': location_id}, None
        )
        self.activity_pool.complete(cr, uid, activity_id, None)
        self.assertEquals(result, None)
        del self.activity_pool.start, self.activity_pool.submit
        del self.activity_pool.complete

    def test_06_get_placements(self):
        cr, uid = self.cr, self.uid
        wiz_id = self.wizard_pool.create(cr, uid, {})
        wiz = self.wizard_pool.browse(cr, uid, wiz_id)
        self.wizard_pool.browse = MagicMock(return_value=wiz)

        result = self.wizard_pool._get_placements(cr, uid, [1])
        self.wizard_pool.browse.assert_called_with(cr, uid, 1, None)
        # check return value is type nh.clinical.patient.placement
        self.assertEqual(type(result), type(self.placement_pool))
        del self.wizard_pool.browse

    def test_07_apply(self):
        cr, uid = self.cr, self.uid
        write_args = {
            'placement_ids': [(6, 0, [1, 2])],
            'recent_placement_ids': [(6, 0, [2])]
        }
        self.wizard_pool.write = MagicMock()
        self.wizard_pool._get_place_patients = MagicMock()
        self.wizard_pool._get_placement_ids = MagicMock(return_value=[1, 2])
        self.wizard_pool._get_recent_placement_ids = MagicMock(
            return_value=[2])

        result = self.wizard_pool.apply(cr, uid, [1, 2])
        self.wizard_pool._get_place_patients.assert_called_with(
            cr, uid, [1, 2], None
        )
        self.assertTrue(self.wizard_pool._get_placement_ids.called)
        self.assertTrue(self.wizard_pool._get_recent_placement_ids.called)
        self.wizard_pool.write.assert_called_with(
            cr, uid, [1, 2], write_args, None
        )
        self.assertEquals(
            result['res_model'],
            'nh.clinical.patient.placement.wizard'
        )
        del self.wizard_pool.write, self.wizard_pool._get_place_patients, \
            self.wizard_pool._get_placement_ids, \
            self.wizard_pool._get_recent_placement_ids

    def test_08_test_get_place_patients(self):
        cr, uid = self.cr, self.uid
        placement_mock = MagicMock(spec=self.placement_pool.__class__.__name__)
        return_value = [
            placement_mock._get_child_mock(),
            placement_mock._get_child_mock(location_id=None)
        ]
        self.wizard_pool._get_placements = MagicMock(return_value=return_value)
        self.wizard_pool._place_patients = MagicMock()

        self.wizard_pool._get_place_patients(cr, uid, [1, 2])
        self.assertEquals(1, self.wizard_pool._place_patients.call_count)
        self.assertTrue(self.wizard_pool._get_placements.called)
        del placement_mock, self.wizard_pool._get_placements
        del self.wizard_pool._place_patients
