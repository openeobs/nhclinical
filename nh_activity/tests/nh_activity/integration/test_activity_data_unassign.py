from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestActivityDataUnassign(TransactionCase):
    """
    Test the unassign method of the nh.activity model
    """

    def setUp(self):
        """
        Set up the tests
        """
        super(TestActivityDataUnassign, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.user_model = self.env['res.users']
        self.activity = self.activity_model.create(
            {
                'user_id': self.uid,
                'data_model': 'test.activity.data.model'
            }
        )

    def test_unassign(self):
        """
        Test that the unassign method removes any assigned users from the
        activity
        """
        self.activity.unassign()
        self.assertFalse(
            self.activity.user_id,
            msg="Activity not unassigned after Unassign"
        )

    def test_no_user_id_present(self):
        """
        Test that the unassign method raises if the activity has no users
        assigned to it
        """
        self.activity.write({'user_id': False})
        with self.assertRaises(except_orm):
            self.activity.unassign()

    def test_not_activity_owner(self):
        """
        Test that the unassign method raises an exception when trying to
        unassign another user from an activity
        """
        user_ids = self.user_model.search([['id', '!=', self.uid]]).ids
        self.activity.write({'user_id': user_ids[0]})
        with self.assertRaises(except_orm):
            self.activity.unassign()

    def test_unassign_completed(self):
        """
        Test that unassign method raises an exception when trying to unassign
        an activity in the state completed
        """
        self.activity.write({'state': 'completed'})
        with self.assertRaises(except_orm):
            self.activity.unassign()

    def test_unassign_cancelled(self):
        """
        Test that unassign method raises an exception when trying to unassign
        an activity in the state cancelled
        """
        self.activity.write({'state': 'cancelled'})
        with self.assertRaises(except_orm):
            self.activity.unassign()

    def test_unassign_locked_activity(self):
        """
        Test that unassign doesn't change the assign status if the activity
        has the assign_locked property set to True
        """
        self.activity.write(
            {
                'assign_locked': True
            }
        )
        self.activity.unassign()
        self.assertTrue(self.activity.assign_locked)
