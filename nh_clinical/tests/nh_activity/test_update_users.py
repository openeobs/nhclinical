from openerp.tests.common import TransactionCase


class TestUpdateUsers(TransactionCase):
    """
    Test that the update_users() method on the nh.activity model is working
    correctly
    """

    def setUp(self):
        """
        Set up the tests
        """
        super(TestUpdateUsers, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.activity_model = self.env['nh.activity']
        self.test_model = self.env['test.activity.data.model1']
        self.test_utils.create_locations()
        self.test_utils.create_users()
        self.other_ward = self.test_utils.other_ward
        self.shift_coordinator = self.test_utils.create_shift_coordinator(
            location_id=self.other_ward.id)
        self.test_utils.create_patient()
        self.spell = self.test_utils.admit_patient()
        self.test_utils.create_placement()
        activity_id = self.test_model.create_activity(
            {
                'parent_id': self.spell.activity_id.id,
                'user_ids': [[6, 0, [self.test_utils.nurse.id]]]
            }, {})
        self.activity = self.activity_model.browse(activity_id)

    def test_empty_user_ids(self):
        """
        Test that when calling update_users() with empty user_ids that it
        just returns True
        """
        self.assertTrue(self.activity_model.update_users([]))

    def test_update_user(self):
        """
        Test that when updating the user that update_users() will remove that
        user from the activities user_ids field
        """
        self.assertTrue(
            self.activity_model.update_users([self.test_utils.nurse.id])
        )
        self.assertFalse(self.activity.user_ids)

    def test_update_location(self):
        self.activity.location_id = self.test_utils.other_ward
        self.assertTrue(
            self.shift_coordinator.id in self.other_ward.user_ids.ids
        )
