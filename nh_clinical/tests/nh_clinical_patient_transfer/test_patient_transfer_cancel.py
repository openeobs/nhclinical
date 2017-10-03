# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase


class TestPatientTransferCancel(TransactionCase):

    def setUp(self):
        super(TestPatientTransferCancel, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.test_utils.admit_and_place_patient()
        self.test_utils.copy_instance_variables(self)

        self.placement_model = self.env['nh.clinical.patient.placement']
        self.bed_id_before_transfer = self.patient.current_location_id

    def call_test(self):
        self.placement_ward_a = self.placement_model.search([
            ('patient_id', '=', self.patient.id),
        ])
        self.placement_ward_a.ensure_one()

        ward_b_code = self.test_utils.other_ward.code
        self.test_utils.transfer_patient(ward_b_code)
        self.bed_id_after_transfer = self.patient.current_location_id

        self.transfer_model = self.env['nh.clinical.patient.transfer']
        transfer = self.transfer_model.search([
            ('patient_id', '=', self.patient.id)
        ])
        transfer.ensure_one()
        transfer.cancel(transfer.activity_id.id)

    def get_open_placements(self):
        return self.placement_model.search([
            ('patient_id', '=', self.patient.id),
            ('state', 'not in', ['completed', 'cancelled'])
        ])

    def test_no_open_placements_when_original_bed_is_available(self):
        """
        If the bed the patient was in before is still
        available, then the new, scheduled placement should
        be cancelled leaving no open placements.
        """
        self.call_test()
        placements = self.get_open_placements()
        self.assertEqual(0, len(placements))

    def test_patient_back_in_original_bed_when_still_available(self):
        """
        If the bed the patient was in before is still
        available, then the patient's current location should
        be the bed they were in before the transfer.
        """
        self.call_test()
        expected = self.bed_id_before_transfer
        actual = self.patient.current_location_id
        self.assertEqual(expected, actual)
