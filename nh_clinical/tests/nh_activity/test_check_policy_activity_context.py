from openerp.tests.common import TransactionCase


class TestCheckPolicyActivityContext(TransactionCase):
    """
    Test that the check_policy_activity_context method of nh.activity.data
    works as intended
    """

    def setUp(self):
        """ Set up the tests """
        super(TestCheckPolicyActivityContext, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.activity_data_model = self.env['nh.activity.data']
        self.test_utils.create_locations()
        self.location = self.test_utils.bed

    def call_test(self):
        """
        Call the check_policy_activity_context method with the context and
        the location_id and return the result

        :return: Result of calling check_policy_activity_context
        """
        return self.activity_data_model.check_policy_activity_context(
            {
                'context': 'eobs'
            },
            location_id=self.location.id
        )

    def call_no_context_test(self):
        """
        Call the check_policy_activity_context method with the context and
        the location_id and return the result

        :return: Result of calling check_policy_activity_context
        """
        return self.activity_data_model.check_policy_activity_context(
            {},
            location_id=self.location.id
        )

    def test_location_context(self):
        """
        Test that if the location has an 'eobs' context and the activity to
        trigger has an 'eobs' context that it returns True
        """
        self.assertTrue(self.call_test())

    def test_location_no_context(self):
        """
        Test that if the location doesn't have a context and the activity
        to trigger has an 'eobs' context that it return False
        """
        self.location.context_ids = None
        self.assertFalse(self.call_test())

    def test_location_wrong_context(self):
        """
        Test that if the location has a 'test' context and the activity to
        trigger has an 'eobs' context that it returns False
        """
        context_model = self.env['nh.clinical.context']
        new_context = context_model.create(
            {
                'name': 'test',
                'models': ['nh.clinical.location']
            }
        )
        self.location.context_ids = [[6, 0, new_context.ids]]
        self.assertFalse(self.call_test())

    def test_activity_no_context(self):
        """
        Test that if the location has an 'eobs' context and the activity to
        trigger has no context that it returns True as it doesn't check the
        contexts match
        """
        self.assertTrue(self.call_no_context_test())

    def test_no_contexts(self):
        """
        Test that if neither the location or the activity to trigger have
        contexts that it returns True as it doesn't check the
        contexts match
        """
        self.location.context_ids = None
        self.assertTrue(self.call_no_context_test())
