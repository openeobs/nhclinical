from openerp.tests.common import TransactionCase


class TestTriggerPolicyCancelOthers(TransactionCase):
    """
    Test that the trigger_policy_cancel others method works as intended
    """

    def setUp(self):
        """ Set up the tests """
        super(TestTriggerPolicyCancelOthers, self).setUp()

    def test_placement_cancel_reason(self):
        """
        Test that when calling trigger_policy_cancel_others() on
        nh.clinical.patient.placement model that it cancels the activity with
        the cancel reason of 'cancelled by placement'
        """
        self.assertTrue(False)

    def test_non_placement_cancel_reason(self):
        """
        Test that when calling trigger_policy_cancel_others() on a model other
        than nh.clinical.patient.placement that it cancels the activity without
        defining a reason
        """
        self.assertTrue(False)

    def test_invalid_model(self):
        """
        Test that an exception is thrown if an invalid model name is passed to
        trigger_policy_cancel_others()
        """
        self.assertTrue(False)
