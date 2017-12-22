from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestActivityDataComplete(TransactionCase):
    """
    Test the complete method of the nh.activity model
    """

    def setUp(self):
        """
        Set up the tests
        """
        super(TestActivityDataComplete, self).setUp()
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
        super(TestActivityDataComplete, self).tearDown()

    def test_complete(self):
        """
        Test that the complete() method moves the state into completed
        """
        self.activity.complete()
        self.assertEqual(
            self.activity.state,
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
            self.activity.date_terminated,
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
            self.activity.terminate_uid.id,
            self.uid,
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
