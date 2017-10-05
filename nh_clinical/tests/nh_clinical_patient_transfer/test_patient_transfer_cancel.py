# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase


class TestPatientTransferCancel(TransactionCase):

    def setUp(self):
        super(TestPatientTransferCancel, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.test_utils.admit_and_place_patient()
        self.test_utils.copy_instance_variables(self)

        self.bed_id_before_transfer = self.patient.current_location_id

    def call_test(self):
        ward_b_code = self.test_utils.other_ward.code
        self.test_utils.transfer_patient(ward_b_code)
        self.bed_id_after_transfer = self.patient.current_location_id

        self.transfer_model = self.env['nh.clinical.patient.transfer']
        transfer = self.transfer_model.search([
            ('patient_id', '=', self.patient.id)
        ])
        transfer.ensure_one()
        transfer.cancel(transfer.activity_id.id)

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
