from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm
from datetime import datetime


class TestSchedule(TransactionCase):
    """ Test the schedule method of the nh.activity model """

    EVENT_TRIGGERED = False
    DATA_MODEL_ACTIVITY_ID = None

    def setUp(self):
        """
        Set up the tests
        """
        super(TestSchedule, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.test_activity_data_model = self.env['test.activity.data.model']
        self.EVENT_TRIGGERED = False
        self.DATA_MODEL_ACTIVITY_ID = None

        def patch_data_model_event(*args, **kwargs):
            self.EVENT_TRIGGERED = True
            self.DATA_MODEL_ACTIVITY_ID = args[3]
            return True

        self.test_activity_data_model._patch_method(
            'schedule',
            patch_data_model_event
        )

        self.activity = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )

    def tearDown(self):
        """
        Remove any patches set up as part of the tests
        """
        self.test_activity_data_model._revert_method('schedule')
        super(TestSchedule, self).tearDown()

    def test_bad_schedule_date(self):
        """
        Test that schedule() raises an exception is the supplied schedule date
        is incorrect
        """
        with self.assertRaises(except_orm):
            self.activity.schedule(2015)

    def test_without_date(self):
        """
        Test that schedule() returns true when not passed a schedule date
        """
        self.assertTrue(self.activity.schedule())

    def test_datetime_as_arg(self):
        """
        Test that schedule accepts datetime.datetime instance for the
        date_scheduled
        """
        test_date = datetime(
            year=1988,
            month=1,
            day=12,
            hour=6,
            minute=0,
            second=0
        )
        self.assertTrue(self.activity.schedule(test_date))

    def test_no_seconds_in_arg(self):
        """
        Test that when passed a datetime string without seconds it accepts it
        and defaults the seconds to 0
        """
        test_date = '1988-01-12 06:00'
        self.assertTrue(self.activity.schedule(test_date))

    def test_only_hours_in_arg(self):
        """
        Test that when passed a datetime string without seconds or minutes it
        accepts it and defaults the seconds and minutes to 0
        """
        test_date = '1988-01-12 06'
        self.assertTrue(self.activity.schedule(test_date))

    def test_just_date_in_arg(self):
        """
        Test that when passed a datetime string that has just the date that it
        accepts this and defaults the date to midnight
        """
        test_date = '1988-01-12'
        self.assertTrue(self.activity.schedule(test_date))

    def test_invalid_format(self):
        """
        Test that when passed a datetime string that doesn't conform to the
        available string formats it raises an exception
        """
        with self.assertRaises(except_orm):
            self.activity.schedule('1988-01')

    def test_calls_data_model_event(self):
        """
        Test that the schedule method on the model defined in the
        data_model of of the activity is called when calling schedule
        on the nh.activity model
        """
        self.activity.schedule()
        self.assertTrue(self.EVENT_TRIGGERED)

    def test_data_model_activity_id(self):
        """
        Test that the schedule method on the model defined in the
        data_model of the activity is called with the activity id
        """
        self.activity.schedule()
        self.assertEqual(
            self.activity.id,
            self.DATA_MODEL_ACTIVITY_ID
        )
