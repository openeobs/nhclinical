from openerp.tests.common import TransactionCase


class TestComplete(TransactionCase):
    """
    Test the complete method of the nh.activity model
    """

    EVENT_TRIGGERED = None

    def setUp(self):
        """
        Set up the tests
        """
        super(TestSubmit, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.datetime_utils = self.env['datetime_utils']
        self.EVENT_TRIGGERED = None

        def patch_data_model_event(*args, **kwargs):
            self.EVENT_TRIGGERED = kwargs.get('callback')
            return True

        def patch_get_current_time(*args, **kwargs):
            return '1988-01-12 06:00:00'

        self.activity_model._patch_method(
            'data_model_event',
            patch_data_model_event
        )
        self.datetime_utils._patch_method(
            'get_current_time',
            patch_get_current_time
        )

        activity_id = self.activity_pool.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )
        self.activity = self.activity_pool.browse(activity_id)

    def tearDown(self):
        """
        Remove any patches set up as part of the tests
        """
        self.activity_model._revert_method('data_model_event')
        self.datetime_utils._revert_method('get_current_time')
        super(TestSubmit, self).tearDown()

    def test_complete(self):
        """
        Test that the complete() method moves the state into completed
        """
        self.activity.complete()
        self.assertEqual(
            activity.state,
            'completed',
            msg="Activity state not updated after Complete"
        )

    def test_date_terminated(self):
        """
        Test that the complete() method sets the date_terminated on the
        activity
        """
        self.activity.complete()
        self.assertEqual(
            activity.date_terminated,
            '1988-01-12 06:00:00',
            msg="Activity date terminated not updated after Complete"
        )

    def test_terminate_uid(self):
        """
        Test that the complete() method sets the terminate_uid to the user
        who called complete
        """
        self.activity.complete()
        self.assertEqual(
            activity.terminate_uid.id,
            uid,
            msg="Activity completion user not updated after Complete"
        )

    def test_already_complete(self):
        """
        Test that the complete() method raises an exception when the activity
        is already in the completed stage
        """
        self.activity.write({'state': 'completed'})
        with self.assertRaises(except_orm):
            self.activity.complete()

    def test_already_cancelled(self):
        """
        Test that the complete() method raises an exception when the activity
        is already in the cancelled stage
        """
        self.activity.write({'state': 'cancelled'})
        with self.assertRaises(except_orm):
            self.activity.complete()

    def test_calls_data_model_event(self):
        """
        Test that the data_model_event decorator is called with the
        update_activity event
        """
        self.activity.complete()
        self.assertEqual(
            self.EVENT_TRIGGERED,
            'complete',
            msg="Event call failed"
        )
