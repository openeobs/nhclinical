from openerp.tests.common import TransactionCase


class TestStart(TransactionCase):
    """
    Test the start() method of the nh.activity model
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

    def test_start(self):
        """
        Test that the start() method moves the activity into the started stage
        """
        self.activity_pool.start()
        self.assertEqual(
            activity.state,
            'started',
            msg="Activity state not updated after Start"
        )

    def test_date_started(self):
        """
        Test that the start() method sets the start date for the activity
        """
        self.activity.start()
        self.assertEqual(
            activity.date_started,
            '1988-01-12 06:00:00',
            msg="Activity date started not updated after Start"
        )

    def test_already_completed(self):
        """
        Test that the start method raises an exception if the activity is
        already completed
        """
        self.activity.write({'state': 'completed'})
        with self.assertRaises(except_orm):
            self.activity.start()

    def test_already_cancelled(self):
        """
        Test that the start method raises an exception if the activity is
        already cancelled
        """
        self.activity.write({'state': 'cancelled'})
        with self.assertRaises(except_orm):
            self.activity.start()

    def test_already_started(self):
        """
        Test that the start method raises an exception if the activity is
        already started
        """
        self.activity.write({'state': 'started'})
        with self.assertRaises(except_orm):
            self.activity.start()

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
            'start',
            msg="Event call failed"
        )
