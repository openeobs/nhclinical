from openerp.tests.common import TransactionCase


class TestTriggerPolicyCreateActivity(TransactionCase):
    """
    Test that the trigger_policy_create_activity method on nh.clinical.data
    creates an activity with the relevant
    """

    def setUp(self):
        """ Set up the tests """
        super(TestTriggerPolicyCreateActivity, self).setUp()

    def test_creates_new_activity(self):
        """
        Test that it creates an activity for the defined model with no case
        defined
        """
        self.assertTrue(False)

    def test_create_activity_with_data(self):
        """
        Test that where a model implements the _get_policy_create_data() method
        that is adds this data to the activity
        """
        self.assertTrue(False)
