from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestActivityDataStart(TransactionCase):
    """
    Test the start() method of the nh.activity model
    """

    def setUp(self):
        """
        Set up the tests
        """
        super(TestActivityDataStart, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.datetime_utils = self.env['datetime_utils']

        def patch_get_current_time(*args, **kwargs):
            return '1988-01-12 06:00:00'

        self.datetime_utils._patch_method(
            'get_current_time',
            patch_get_current_time
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
        self.datetime_utils._revert_method('get_current_time')
        super(TestActivityDataStart, self).tearDown()

    def test_start(self):
        """
        Test that the start() method moves the activity into the started stage
        """
        self.activity.start()
        self.assertEqual(
            self.activity.state,
            'started',
            msg="Activity state not updated after Start"
        )

    def test_date_started(self):
        """
        Test that the start() method sets the start date for the activity
        """
        self.activity.start()
        self.assertEqual(
            self.activity.date_started,
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
