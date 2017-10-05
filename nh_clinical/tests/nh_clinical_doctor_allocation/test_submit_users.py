# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase


class TestSubmitUsers(TransactionCase):

    def setUp(self):
        super(TestSubmitUsers, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.test_utils.create_locations()
        location_ids = [
            self.test_utils.ward.id,
            self.test_utils.other_ward.id,
            self.test_utils.bed.id,
            self.test_utils.other_bed.id
        ]
        self.test_utils.create_doctor(location_ids)
        self.doctor = self.test_utils.doctor

    def test_doctor_is_not_deallocated_from_any_existing_locations(self):
        ward_1 = self.test_utils.ward
        ward_2 = self.test_utils.other_ward
        ward_3 = self.test_utils.create_location(
            'ward', self.test_utils.hospital.id)
        ward_3_shift_coordinator = self.test_utils.create_shift_coordinator(
            ward_3.id)

        doctor_allocation_model = self.env['nh.clinical.doctor.allocation']
        doctor_allocation_wizard = doctor_allocation_model.sudo(
            ward_3_shift_coordinator).create({
                'user_ids': [([6, 0, [self.test_utils.doctor.id]])],
                'ward_id': ward_3.id
            })
        doctor_allocation_wizard.submit_users()

        self.assertIn(ward_1, self.doctor.location_ids)
        self.assertIn(ward_2, self.doctor.location_ids)
