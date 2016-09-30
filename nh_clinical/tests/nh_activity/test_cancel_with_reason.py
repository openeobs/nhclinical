# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase
from openerp.osv.osv import except_osv
from openerp.exceptions import MissingError


class TestCancelWithReason(TransactionCase):

    def setUp(self):
        super(TestCancelWithReason, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']

        self.activity = self.activity_model.create({
            'data_model': 'nh.clinical.spell'
        })

        self.cancel_reason_placement = \
            self.browse_ref('nh_clinical.cancel_reason_placement')

    def test_activity_is_cancelled(self):
        self.activity_model.cancel_with_reason(
            self.activity.id, self.cancel_reason_placement.id
        )

        self.assertEqual(self.activity.state, 'cancelled')

    def test_activity_has_cancellation_reason(self):
        self.activity_model.cancel_with_reason(
            self.activity.id, self.cancel_reason_placement.id
        )

        self.assertEqual(
            self.activity.cancel_reason_id, self.cancel_reason_placement
        )

    def test_none_activity_id(self):
        with self.assertRaises(except_osv):
            self.activity_model.cancel_with_reason(
                None, self.cancel_reason_placement.id
            )

    def test_non_existent_activity_id(self):
        max_id = 2147483647

        with self.assertRaises(MissingError):
            self.activity_model.cancel_with_reason(
                max_id, self.cancel_reason_placement.id
            )
