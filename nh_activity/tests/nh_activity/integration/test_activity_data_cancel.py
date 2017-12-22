from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestActivityDataCancel(TransactionCase):
    """ Test the cancel() method of the nh.activity model """

    def setUp(self):
        """
        Set up the tests
        """
        super(TestActivityDataCancel, self).setUp()
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
        super(TestActivityDataCancel, self).tearDown()

    def test_cancel(self):
        """
        Test that cancel sets the state of the activity to cancelled
        """
        self.activity.cancel()
        self.assertEqual(
            self.activity.state,
            'cancelled',
            msg="Activity state not updated after Cancel"
        )

    def test_date_terminated(self):
        """
        Test that cancel() sets the date_terminated on the activity being
        cancelled
        """
        self.activity.cancel()
        self.assertEqual(
            self.activity.date_terminated,
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
            self.activity.terminate_uid.id,
            self.uid,
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
