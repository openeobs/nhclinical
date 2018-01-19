from openerp.tests.common import TransactionCase


class TestUpdateSpellUsers(TransactionCase):
    """
    Test that the update_spell_users method is working correctly
    """

    def setUp(self):
        """ Set up the tests """
        super(TestUpdateSpellUsers, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.activity_model = self.env['nh.activity']
        self.test_utils.create_locations()
        self.test_utils.create_users()
        self.other_ward = self.test_utils.other_ward
        self.shift_coordinator = self.test_utils.create_shift_coordinator(
            location_id=self.other_ward.id)
        self.test_utils.create_patient()
        self.spell = self.test_utils.admit_patient()
        self.test_utils.create_placement()

    def test_empty_user_ids(self):
        """
        Test when passed empty user IDs that it just returns True
        """
        self.assertTrue(self.activity_model.update_spell_users())

    def test_updates_location(self):
        """
        Test that updating the location on the spell that it updates the
        user_ids to include the shift coordinator for that ward
        """
        self.spell.activity_id.location_id = self.other_ward
        self.assertTrue(
            self.shift_coordinator.id
            in self.spell.activity_id.user_ids.ids
        )
