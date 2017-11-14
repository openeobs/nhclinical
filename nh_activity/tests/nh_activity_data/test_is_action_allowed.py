from openerp.tests.common import TransactionCase


class TestIsActionAllowed(TransactionCase):
    """
    Test the is_action_allowed method on the nh.activity model
    """

    def setUp(self):
        """
        Set up the tests
        """
        super(TestSubmit, self).setUp()
        self.test_model = self.env['test.activity.data.model']

    def test_new_to_schedule(self):
        """
        Test that the new -> schedule transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('new', 'schedule')
        )

    def test_scheduled_to_schedule(self):
        """
        Test that the scheduled -> schedule transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('scheduled', 'schedule')
        )

    def test_started_to_schedule(self):
        """
        Test that the started -> schedule transition is not allowed
        """
        self.assertFalse(
            self.test_model.is_action_allowed('started', 'schedule')
        )

    def test_completed_to_schedule(self):
        """
        Test that the completed -> schedule transition is not allowed
        """
        self.assertFalse(
            self.test_model.is_action_allowed('completed', 'schedule')
        )

    def test_cancelled_to_schedule(self):
        """
        Test that the cancelled -> schedule transition is not allowed
        """
        self.assertFalse(
            self.test_model.is_action_allowed('cancelled', 'schedule')
        )

    def test_new_to_start(self):
        """
        Test that the new -> start transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('new', 'start')
        )

    def test_scheduled_to_start(self):
        """
        Test that the scheduled -> start transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('scheduled', 'start')
        )

    def test_started_to_start(self):
        """
        Test that the started -> start transition is not allowed
        """
        self.assertFalse(
            self.test_model.is_action_allowed('started', 'start')
        )

    def test_completed_to_start(self):
        """
        Test that the completed -> start transition is not allowed
        """
        self.assertFalse(
            self.test_model.is_action_allowed('completed', 'start')
        )

    def test_canceled_to_start(self):
        """
        Test that the canceled -> start transition is not allowed
        """
        self.assertFalse(
            self.test_model.is_action_allowed('canceled', 'start')
        )

    def test_new_to_complete(self):
        """
        Test that the new -> complete transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('new', 'complete')
        )

    def test_scheduled_to_complete(self):
        """
        Test that the scheduled -> complete transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('scheduled', 'complete')
        )

    def test_started_to_complete(self):
        """
        Test that the started -> complete transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('started', 'complete')
        )

    def test_completed_to_complete(self):
        """
        Test that the completed -> complete transition is not allowed
        """
        self.assertFalse(
            self.test_model.is_action_allowed('completed', 'complete')
        )

    def test_cancelled_to_complete(self):
        """
        Test that the cancelled -> complete transition is not allowed
        """
        self.assertFalse(
            self.test_model.is_action_allowed('cancelled', 'complete')
        )

    def test_new_to_cancel(self):
        """
        Test that the new -> cancel transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('new', 'cancel')
        )

    def test_scheduled_to_cancel(self):
        """
        Test that the scheduled -> cancel transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('scheduled', 'cancel')
        )

    def test_started_to_cancel(self):
        """
        Test that the started -> cancel transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('started', 'cancel')
        )

    def test_completed_to_cancel(self):
        """
        Test that the completed -> cancel transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('completed', 'cancel')
        )

    def test_cancelled_to_cancel(self):
        """
        Test that the cancelled -> cancel transition is allowed
        """
        self.assertFalse(
            self.test_model.is_action_allowed('cancelled', 'cancel')
        )

    def test_new_to_submit(self):
        """
        Test that the new -> submit transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('new', 'submit')
        )

    def test_scheduled_to_submit(self):
        """
        Test that the scheduled -> submit transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('scheduled', 'submit')
        )

    def test_started_to_submit(self):
        """
        Test that the started -> submit transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('started', 'submit')
        )

    def test_completed_to_submit(self):
        """
        Test that the completed -> submit transition is not allowed
        """
        self.assertFalse(
            self.test_model.is_action_allowed('completed', 'submit')
        )

    def test_cancelled_to_submit(self):
        """
        Test that the cancelled -> submit transition is not allowed
        """
        self.assertFalse(
            self.test_model.is_action_allowed('cancelled', 'submit')
        )

    def test_new_to_assign(self):
        """
        Test that the new -> assign transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('new', 'assign')
        )

    def test_scheduled_to_assign(self):
        """
        Test that the scheduled -> assign transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('scheduled', 'assign')
        )

    def test_started_to_assign(self):
        """
        Test that the started -> assign transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('started', 'assign')
        )

    def test_completed_to_assign(self):
        """
        Test that the completed -> assign transition is not allowed
        """
        self.assertFalse(
            self.test_model.is_action_allowed('completed', 'assign')
        )

    def test_cancelled_to_assign(self):
        """
        Test that the cancelled -> assign transition is not allowed
        """
        self.assertFalse(
            self.test_model.is_action_allowed('cancelled', 'assign')
        )

    def test_new_to_unassign(self):
        """
        Test that the new -> unassign transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('new', 'unassign')
        )

    def test_scheduled_to_unassign(self):
        """
        Test that the scheduled -> unassign transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('scheduled', 'unassign')
        )

    def test_started_to_unassign(self):
        """
        Test that the started -> unassign transition is allowed
        """
        self.assertTrue(
            self.test_model.is_action_allowed('started', 'unassign')
        )

    def test_completed_to_unassign(self):
        """
        Test that the completed -> unassign transition is not allowed
        """
        self.assertFalse(
            self.test_model.is_action_allowed('completed', 'unassign')
        )

    def test_cancelled_to_unassign(self):
        """
        Test that the cancelled -> unassign transition is not allowed
        """
        self.assertFalse(
            self.test_model.is_action_allowed('cancelled', 'unassign')
        )
