from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestCheckAction(TransactionCase):
    """
    Test the check_action method on the nh.activity model
    """

    def setUp(self):
        """
        Set up the tests
        """
        super(TestCheckAction, self).setUp()
        self.test_model = self.env['test.activity.data.model']

    def test_check_action_new_to_schedule(self):
        """
        Test that check_action returns True for new -> scheduled transition
        """
        self.assertTrue(self.test_model.check_action('new', 'schedule'))

    def test_check_action_scheduled_to_schedule(self):
        """
        Test that check_action returns True for schedule -> scheduled
        transition
        """
        self.assertTrue(self.test_model.check_action('scheduled', 'schedule'))

    def test_check_action_started_to_schedule(self):
        """
        Test that check_action raises an exception for started -> scheduled
        transition
        """
        with self.assertRaises(except_orm):
            self.test_model.check_action('started', 'schedule')

    def test_check_action_completed_to_schedule(self):
        """
        Test that check_action raises an exception for completd -> scheduled
        transition
        """
        with self.assertRaises(except_orm):
            self.test_model.check_action('completed', 'schedule')

    def test_check_action_cancelled_to_schedule(self):
        """
        Test that check_action raises an exception for cancelled -> scheduled
        transition
        """
        with self.assertRaises(except_orm):
            self.test_model.check_action('cancelled', 'schedule')

    def test_check_action_new_to_start(self):
        """
        Test that check_action returns True for new -> startd transition
        """
        self.assertTrue(self.test_model.check_action('new', 'start'))

    def test_check_action_startd_to_start(self):
        """
        Test that check_action returns True for start -> startd
        transition
        """
        self.assertTrue(self.test_model.check_action('scheduled', 'start'))

    def test_check_action_started_to_start(self):
        """
        Test that check_action raises an exception for started -> startd
        transition
        """
        with self.assertRaises(except_orm):
            self.test_model.check_action('started', 'start')

    def test_check_action_completed_to_start(self):
        """
        Test that check_action raises an exception for completd -> startd
        transition
        """
        with self.assertRaises(except_orm):
            self.test_model.check_action('completed', 'start')

    def test_check_action_cancelled_to_start(self):
        """
        Test that check_action raises an exception for cancelled -> startd
        transition
        """
        with self.assertRaises(except_orm):
            self.test_model.check_action('cancelled', 'start')

    def test_check_action_new_to_complete(self):
        """
        Test that check_action returns True for new -> completed transition
        """
        self.assertTrue(self.test_model.check_action('new', 'complete'))

    def test_check_action_scheduled_to_complete(self):
        """
        Test that check_action returns True for scheduled -> completed
        transition
        """
        self.assertTrue(self.test_model.check_action('scheduled', 'complete'))

    def test_check_action_started_to_complete(self):
        """
        Test that check_action returns True for started -> complete transition
        """
        self.assertTrue(self.test_model.check_action('started', 'complete'))

    def test_check_action_completed_to_complete(self):
        """
        Test that check_action raises an exception for completed -> complete
        transition
        """
        with self.assertRaises(except_orm):
            self.test_model.check_action('completed', 'complete')

    def test_check_action_cancelled_to_complete(self):
        """
        Test that check_action raises an exception for cancelled -> completed
        transition
        """
        with self.assertRaises(except_orm):
            self.test_model.check_action('cancelled', 'complete')

    def test_check_action_new_to_cancel(self):
        """
        Test that check_action returns True for new -> canceld transition
        """
        self.assertTrue(self.test_model.check_action('new', 'cancel'))

    def test_check_action_scheduled_to_cancel(self):
        """
        Test that check_action returns True for schedule -> canceld
        transition
        """
        self.assertTrue(self.test_model.check_action('scheduled', 'cancel'))

    def test_check_action_started_to_cancel(self):
        """
        Test that check_action returns True for started -> cancelled transition
        """
        self.assertTrue(self.test_model.check_action('started', 'cancel'))

    def test_check_action_completed_to_cancel(self):
        """
        Test that check_action returns True for completed -> cancelled
        """
        self.assertTrue(self.test_model.check_action('completed', 'cancel'))

    def test_check_action_cancelled_to_cancel(self):
        """
        Test that check_action raises an exception for cancelled -> canceld
        transition
        """
        with self.assertRaises(except_orm):
            self.test_model.check_action('cancelled', 'cancel')

    def test_check_action_new_to_submit(self):
        """
        Test that check_action returns True for new -> submitd transition
        """
        self.assertTrue(self.test_model.check_action('new', 'submit'))

    def test_check_action_scheduled_to_submit(self):
        """
        Test that check_action returns True for schedule -> submitd
        transition
        """
        self.assertTrue(self.test_model.check_action('scheduled', 'submit'))

    def test_check_action_started_to_submit(self):
        """
        Test that check_action returns True for started -> submit transition
        """
        self.assertTrue(self.test_model.check_action('started', 'submit'))

    def test_check_action_completed_to_submit(self):
        """
        Test that check_action raises an exception for completd -> submitd
        transition
        """
        with self.assertRaises(except_orm):
            self.test_model.check_action('completed', 'submit')

    def test_check_action_cancelled_to_submit(self):
        """
        Test that check_action raises an exception for cancelled -> submitd
        transition
        """
        with self.assertRaises(except_orm):
            self.test_model.check_action('cancelled', 'submit')

    def test_check_action_new_to_assign(self):
        """
        Test that check_action returns True for new -> assignd transition
        """
        self.assertTrue(self.test_model.check_action('new', 'assign'))

    def test_check_action_scheduled_to_assign(self):
        """
        Test that check_action returns True for schedule -> assignd
        transition
        """
        self.assertTrue(self.test_model.check_action('scheduled', 'assign'))

    def test_check_action_started_to_assign(self):
        """
        Test that check_action returns True for started -> assign transition
        """
        self.assertTrue(self.test_model.check_action('started', 'assign'))

    def test_check_action_completed_to_assign(self):
        """
        Test that check_action raises an exception for completd -> assignd
        transition
        """
        with self.assertRaises(except_orm):
            self.test_model.check_action('completed', 'assign')

    def test_check_action_cancelled_to_assign(self):
        """
        Test that check_action raises an exception for cancelled -> assignd
        transition
        """
        with self.assertRaises(except_orm):
            self.test_model.check_action('cancelled', 'assign')

    def test_check_action_new_to_unassign(self):
        """
        Test that check_action returns True for new -> unassignd transition
        """
        self.assertTrue(self.test_model.check_action('new', 'unassign'))

    def test_check_action_scheduled_to_unassign(self):
        """
        Test that check_action returns True for schedule -> unassignd
        transition
        """
        self.assertTrue(self.test_model.check_action('scheduled', 'unassign'))

    def test_check_action_started_to_unassign(self):
        """
        Test that check_action returns True for started -> unassign transition
        """
        self.assertTrue(self.test_model.check_action('started', 'unassign'))

    def test_check_action_completed_to_unassign(self):
        """
        Test that check_action raises an exception for completd -> unassignd
        transition
        """
        with self.assertRaises(except_orm):
            self.test_model.check_action('completed', 'unassign')

    def test_check_action_cancelled_to_unassign(self):
        """
        Test that check_action raises an exception for cancelled -> unassignd
        transition
        """
        with self.assertRaises(except_orm):
            self.test_model.check_action('cancelled', 'unassign')
