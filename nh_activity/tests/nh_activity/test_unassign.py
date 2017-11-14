from openerp.tests.common import TransactionCase


class TestUnassign(TransactionCase):
    """
    Test the unassign method of the nh.activity model
    """

    EVENT_TRIGGERED = None
    WRITE_CALLED = False

    def setUp(self):
        """
        Set up the tests
        """
        super(TestSubmit, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.user_model = self.env['res.users']
        self.EVENT_TRIGGERED = None
        self.WRITE_CALLED = False

        def patch_data_model_event(*args, **kwargs):
            self.EVENT_TRIGGERED = kwargs.get('callback')
            return True

        def mock_write(*args, **kwargs):
            self.WRITE_CALLED = True
            return mock_write.origin(*args, **kwargs)

        self.activity_model._patch_method(
            'data_model_event',
            patch_data_model_event
        )
        self.activity_model._patch_method(
            'write',
            mock_write
        )

        activity_id = self.activity_pool.create(
            {
                'user_id': self.uid,
                'data_model': 'test.activity.data.model'
            }
        )
        self.activity = self.activity_pool.browse(activity_id)

    def tearDown(self):
        """
        Remove any patches set up as part of the tests
        """
        self.activity_model._revert_method('data_model_event')
        self.activity_model._revert_method('write')
        super(TestSubmit, self).tearDown()

    def test_unassign(self):
        """
        Test that the unassign method removes any assigned users from the
        activity
        """
        self.activity.unassign()
        self.assertFalse(
            activity.user_id,
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
        user_ids = self.user_model.search(cr, uid, [['id', '!=', uid]])
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
        self.WRITE_CALLED = False
        self.activity.unassign()
        self.assertTrue(self.activity.assign_locked)
        self.assertFalse(self.WRITE_CALLED)

    def test_calls_data_model_event(self):
        """
        Test that the data_model_event decorator is called with the
        update_activity event
        """
        activity_id = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )
        self.activity_model.update_activity(activity_id)
        self.assertEqual(
            self.EVENT_TRIGGERED,
            'unassign',
            msg="Event call failed"
        )
