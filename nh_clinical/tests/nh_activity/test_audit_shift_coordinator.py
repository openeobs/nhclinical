from openerp.tests.common import TransactionCase


class TestAuditShiftCoordinator(TransactionCase):
    """
    Test that the audit_shift_coordinator() method on nh.activity.data works
    correctly
    """

    def setUp(self):
        """
        Set up the test
        """
        super(TestAuditShiftCoordinator, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.activity_model = self.env['nh.activity']
        self.test_model = self.env['test.activity.data.model1']
        self.test_utils.admit_and_place_patient()
        self.shift_coordinator = self.test_utils.create_shift_coordinator()
        self.spell_activity = self.test_utils.spell.activity_id

    def test_no_location(self):
        """
        Test that when there's no location associated with the activity that
        audit_shift_coordinator returns False
        """
        self.spell_activity.location_id = False
        self.assertFalse(self.test_utils.spell._audit_shift_coordinator(
            self.spell_activity.id)
        )

    def test_sets_ward_for_bed(self):
        """
        Test that when the location associated with the activity is a bed
        and the ward the bed is in has a shift coordinator associated with it
        that it updates the activity to have the ward_manager_id set to the
        shift coordinators user ID
        """
        self.assertFalse(self.spell_activity.ward_manager_id)
        self.spell_activity.location_id = self.test_utils.bed
        self.assertTrue(
            self.test_utils.spell._audit_shift_coordinator(
                self.spell_activity.id
            )
        )
        self.assertTrue(
            self.shift_coordinator.id
            in self.spell_activity.ward_manager_id.ids
        )

    def test_sets_ward(self):
        """
        Test that when the location associated with the activity is a ward and
        the ward has a shift coordinator associated with it that it updates the
        activity to have the ward_manager_id set to the shift coordinator's
        user ID
        """
        self.assertFalse(self.spell_activity.ward_manager_id)
        self.spell_activity.location_id = self.test_utils.ward
        self.assertTrue(
            self.test_utils.spell._audit_shift_coordinator(
                self.spell_activity.id
            )
        )
        self.assertTrue(
            self.shift_coordinator.id
            in self.spell_activity.ward_manager_id.ids
        )

    def test_no_shift_coordinator(self):
        """
        Test that when the location associated with the activity has no
        shift coordinator that _audit_shift_coordinator() returns False
        and doesn't set a ward_manager_id
        """
        self.test_utils.ward.ward_manager_id = False
        self.shift_coordinator.location_ids = False
        self.spell_activity.location_id = self.test_utils.ward
        self.assertFalse(
            self.test_utils.spell._audit_shift_coordinator(
                self.spell_activity.id
            )
        )

    def test_list_sent(self):
        """
        Test that when passing id as [id] it doesn't break and resolves the id
        to an int. It will break if multiple IDs passed as requires a singleton
        """
        self.assertTrue(
            self.test_utils.spell._audit_shift_coordinator(
                [self.spell_activity.id]
            )
        )
