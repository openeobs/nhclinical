from openerp.tests.common import TransactionCase


class TestCancel(TransactionCase):
    """ Test the cancel() method of the nh.activity model """

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

    def test_cancel(self):
        """
        Test that cancel sets the state of the activity to cancelled
        """
        self.activity.cancel()
        self.assertEqual(
            activity.state,
            'cancelled',
            msg="Activity state not updated after Cancel"
        )

    def test_date_terminated(self):
        """
        Test that cancel() sets the date_terminated on the activity being
        cancelled
        """
        self.activity.cancel()
        self.assertAlmostEqual(
            activity.date_terminated,
            '1988-01-12 06:00:00',
            msg="Activity date terminated not updated after Cancel"
        )

    def test_terminate_uid(self):
        """
        Test that cancel() sets the terminate_uid on the activity being
        cancelled
        """
        self.activity.cancel()
        self.assertEqual(
            activity.terminate_uid.id,
            uid,
            msg="Activity completion user not updated after Cancel"
        )

    def test_already_cancelled(self):
        """
        Test that cancel() raises an exception if the activity is already
        cancelled
        """
        self.activity.write({'state': 'cancelled'})
        with self.assertRaises(except_orm):
            self.activity.cancel()

    def test_already_completed(self):
        """
        Test that cancel() raises an exception if the activity is already
        completed
        """
        self.activity.write({'state': 'completed'})
        with self.assertRaises(except_orm):
            self.activity.cancel()

    def test_calls_data_model_event(self):
        """
        Test that the data_model_event decorator is called with the
        cancel event
        """
        self.activity.cancel()
        self.assertEqual(
            self.EVENT_TRIGGERED,
            'cancel',
            msg="Event call failed"
        )
