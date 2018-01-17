from openerp.tests.common import TransactionCase


class TestTriggerPolicyActivity(TransactionCase):
    """
    Test the trigger_policy_activity method of the nh.activity.data model
    """

    def setUp(self):
        super(TestTriggerPolicyActivity, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.test_utils.admit_and_place_patient()

    def test_cancel_others(self):
        """
        Test that when set to cancel others that the triggering of the policy
        cancels the currently open activities of the same type
        """
        self.assertTrue(False)

    def test_schedules_activity(self):
        """
        Test that when no type is set that the triggered activity is scheduled
        for an hours time
        """
        self.assertTrue(False)

    def test_schedules_recurring_activity(self):
        """
        Test that when the type is set to recurring that the triggered
        activity is scheduled with the recurrence configuration for that
        activity
        """
        self.assertTrue(False)

    def test_starts_activity(self):
        """
        Test that when the type is set to start that the triggered activity
        is started
        """
        self.assertTrue(False)

    def test_completes_activity(self):
        """
        Test that when the type is set to complete that the triggered activity
        is completed
        """
        self.assertTrue(False)

    def test_completes_activity_with_data(self):
        """
        Test that when the type is set to complete and data is also passed that
        the triggered activity has that data submitted against it and it is
        then completed
        """
        self.assertTrue(False)
