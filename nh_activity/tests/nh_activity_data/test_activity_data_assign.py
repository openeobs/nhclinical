from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestActivityDataAssign(TransactionCase):
    """
    Test the assign() method of the nh.activity_data model. This method
    is invoked via a decorator on the assign() method of the nh.activity model
    """

    def setUp(self):
        """
        Set up the tests
        """
        super(TestActivityDataAssign, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.user_model = self.env['res.users']
        self.activity = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )

    def test_assign(self):
        """
        Test that assign sets the user_id associated with the activity to the
        defined user_id
        """
        self.activity.assign(self.uid)
        self.assertEqual(
            self.activity.user_id.id,
            self.uid,
            msg="User id not updated after Assign"
        )

    def test_assign_locked(self):
        """
        Test that when an activity is assigned it sets the assign_locked
        property on the activity
        """
        self.activity.write({'user_id': self.uid})
        self.activity.assign(self.uid)
        self.assertEquals(self.activity.assign_locked, True)

    def test_already_assigned(self):
        """
        Test that assign raises an exception if trying to assign an activity
        that has already been assigned
        """
        self.activity.assign(self.uid)
        user_ids = self.user_model.search([['id', '!=', self.uid]])
        with self.assertRaises(except_orm):
            self.activity.assign(user_ids[0])

    def test_assign_completed(self):
        """
        Test that assign raises an exception when trying to assign an activity
        that is already completed
        """
        self.activity.write({'state': 'completed'})
        with self.assertRaises(except_orm):
            self.activity.assign(self.uid)

    def test_assign_cancelled(self):
        """
        Test that assign raises an exception when trying to assign an activity
        that is already cancelled
        """
        self.activity.write({'state': 'cancelled'})
        with self.assertRaises(except_orm):
            self.activity.assign(self.uid)
