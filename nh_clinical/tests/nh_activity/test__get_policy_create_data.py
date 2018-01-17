from openerp.tests.common import TransactionCase


class TestGetPolicyCreateData(TransactionCase):
    """
    Test that the _get_policy_create_data method returns a dictionary that can
    be used
    """

    def setUp(self):
        """ Set up the tests """
        super(TestGetPolicyCreateData, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.test_policy_model = self.env['test.activity.data.model0']
        self.test_no_policy_model = self.env['test.activity.data.model3']
        self.test_utils.admit_and_place_patient()
        activity_info = {
            'parent_id': self.test_utils.spell.id
        }
        activity_data = {
            'field1': 'Test',
            'frequency': 10,
            'patient_id': self.test_utils.patient.id
        }
        policy_activity_id = self.test_policy_model.create_activity(
            activity_info, activity_data)
        no_policy_activity_id = self.test_policy_model.create_activity(
            activity_info, activity_data)
        self.policy_activity = self.test_policy_model.search(
            [
                ['activity_id', '=', policy_activity_id]
            ])
        self.no_policy_activity = self.test_no_policy_model.search(
            [
                ['activity_id', '=', no_policy_activity_id]
            ])

    def test_no_subclass_override(self):
        """
        Test that the method returns a dictionary with nothing in it when
        the _get_policy_create_data() method isn't overriden
        """
        result = self.no_policy_activity._get_policy_create_data()
        self.assertEqual(result, {})

    def test_subclass_override_case_1(self):
        """
        Test that when the subclass overrides the _get_policy_create_data()
        method and adds case based logic that the correct value is returned.

        In this test the model under test is ``test.activity.data.model0``
        which when using case 1 will return a dictionary with the field and
        frequency keys
        """
        result = self.policy_activity._get_policy_create_data(case=1)
        self.assertEqual(
            result,
            {
                'field1': 'Test',
                'frequency': 10
            }
        )

    def test_subclass_override_case_2(self):
        """
        Test that when the subclass overrides the _get_policy_create_data()
        method and adds case based logic that the correct value is returned.

        In this test the model under test is ``test.activity.data.model0``
        which when using case 2 will return a dictionary with the field but
        not the frequency keys
        """
        result = self.policy_activity._get_policy_create_data(case=2)
        self.assertEqual(
            result,
            {
                'field1': 'Test'
            }
        )
