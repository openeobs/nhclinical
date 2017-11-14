from openerp.tests.common import TransactionCase


class TestSchedule(TransactionCase):
    """ Test the schedule method of the nh.activity model """

    EVENT_TRIGGERED = None

    def setUp(self):
        """
        Set up the tests
        """
        super(TestSubmit, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.EVENT_TRIGGERED = None

        def patch_data_model_event(*args, **kwargs):
            self.EVENT_TRIGGERED = kwargs.get('callback')
            return True

        self.activity_model._patch_method(
            'data_model_event',
            patch_data_model_event
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
        super(TestSubmit, self).tearDown()

    def test_schedule(self):
        """
        Test that schedule() changes the state of the activity to scheduled
        """
        test_date = '1988-01-12 06:00:00'
        self.activity.schedule(test_date)
        self.assertEqual(
            self.activity.state,
            'scheduled',
            msg="Activity state not updated after schedule"
        )

    def test_date_scheduled(self):
        """
        Test that schedule() sets the date_scheduled property on the sheduled
        activity
        """
        test_date = '1988-01-12 06:00:00'
        self.activity.schedule(test_date)
        self.assertEqual(
            activity.date_scheduled,
            test_date,
            msg="Activity date_scheduled not updated after schedule"
        )

    def test_bad_schedule_date(self):
        """
        Test that schedule() raises an exception is the supplied schedule date
        is incorrect
        """
        with self.assertRaises(except_orm):
            self.activity.schedule(2015)

    def test_already_date_scheduled(self):
        """
        Test that schedule() moves the activity into scheduled if the activity
        already has the date_scheduled property set
        """
        test_date = '2015-10-10 12:00:00'
        self.activity.write({'date_scheduled': test_date})
        self.activity.schedule()
        self.assertEqual(
            activity.state,
            'scheduled',
            msg="Activity state not updated after schedule"
        )

    def test_doesnt_change_date_scheduled(self):
        """
        Test that schedule() doesn't change the already scheduled date when
        being called on an activity with a schedule date
        :return:
        """
        test_date = '2015-10-10 12:00:00'
        self.activity.write({'date_scheduled': test_date})
        self.activity.schedule()
        self.assertEqual(
            activity.date_scheduled,
            test_date,
            msg="Activity date_scheduled not updated after schedule"
        )

    def test_without_date(self):
        """
        Test that schedule() raises an exception if it's called without a
        date being supplied and the activity doesn't currently have a
        date_scheduled property set
        """
        with self.assertRaises(except_orm):
            self.activity.schedule()

    def test_datetime_as_arg(self):
        """
        Test that schedule accepts datetime.datetime instance for the
        date_scheduled
        """
        test_date = dt(
            year=1988,
            month=1,
            day=12,
            hour=6,
            minute=0,
            second=0
        )
        self.activity_pool.schedule(test_date)
        self.assertEqual(
            activity.date_scheduled,
            '1988-01-12 06:00:00',
            msg="Activity date_scheduled not updated after schedule"
        )

    def test_no_seconds_in_arg(self):
        """
        Test that when passed a datetime string without seconds it accepts it
        and defaults the seconds to 0
        """
        test_date = '1988-01-12 06:00'
        self.activity_pool.schedule(test_date)
        self.assertEqual(
            activity.date_scheduled,
            '1988-01-12 06:00:00',
            msg="Activity date_scheduled not updated after schedule"
        )

    def test_just_date_in_arg(self):
        """
        Test that when passed a datetime string that has just the date that it
        accepts this and defaults the date to midnight
        """
        test_date = '1988-01-12'
        self.activity_pool.schedule(test_date)
        self.assertEqual(
            activity.date_scheduled,
            '1988-01-12 00:00:00',
            msg="Activity date_scheduled not updated after schedule"
        )

    def test_already_started(self):
        """
        Test that when calling schedule() on an activity that is already in
        the started state that it raises an error
        """
        self.activity.write({'state': 'started'})
        with self.assertRaises(except_orm):
            self.activity.schedule()

    def test_already_completed(self):
        """
        Test that when calling schedule() on an activity that is already in
        the completed state that it raises an error
        """
        self.activity.write({'state': 'completed'})
        with self.assertRaises(except_orm):
            self.activity.schedule()

    def test_already_cancelled(self):
        """
        Test that when calling schedule() on an activity that is already in
        the cancelled state that it raises an error
        """
        self.activity.write({'state': 'cancelled'})
        with self.assertRaises(except_orm):
            self.activity.schedule()

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
            'schedule',
            msg="Event call failed"
        )
