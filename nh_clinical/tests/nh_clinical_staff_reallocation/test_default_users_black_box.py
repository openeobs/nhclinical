from openerp.tests.common import TransactionCase


class TestStaffReallocationDefaultUsers(TransactionCase):

    # EOBS-549
    def test_returns_all_users_added_to_roll_call(self):
        """
        Ensure that all users added to the roll call of a shift are present
        in subsequent allocation records.

        The particular reason this regression test came about was because users
        who were added to the roll call but not allocated directly to beds did
        not appear in subsequent allocation wizards.
        """
        test_utils = self.env['nh.clinical.test_utils']
        test_utils.admit_and_place_patient()  # Creates locations and users.
        self.shift_coordinator = test_utils.create_shift_coordinator()
        self.nurse = test_utils.nurse
        self.hca = test_utils.hca
        self.nurse_2 = test_utils.create_nurse(allocate=False)
        self.hca_2 = test_utils.create_hca(allocate=False)

        expected_users_on_shift_ids = map(
            lambda e: e.id, [
                self.nurse, self.nurse_2, self.hca, self.hca_2
            ]
        )
        user_model = self.env['res.users']
        # Expected needs to be a recordset to match actual result type.
        expected_users_on_shift = user_model.browse(expected_users_on_shift_ids)

        allocation_model = self.env['nh.clinical.staff.allocation']
        allocation = allocation_model.create({})
        # Have to assign users after creation because setting in creation
        # dictionary does not work. Not sure why.
        allocation.ward_id = test_utils.ward.id
        allocation.user_ids = expected_users_on_shift
        allocation.complete()

        reallocation_model = self.env['nh.clinical.staff.reallocation']
        reallocation = \
            reallocation_model.sudo(self.shift_coordinator).create({})
        actual_users_on_shift = reallocation.user_ids

        self.assertEqual(expected_users_on_shift, actual_users_on_shift)
