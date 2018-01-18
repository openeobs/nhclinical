from openerp.tests.common import TransactionCase


class TestTriggerPolicyActivity(TransactionCase):
    """
    Test the trigger_policy_activity method of the nh.activity.data model
    """

    def setUp(self):
        super(TestTriggerPolicyActivity, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.activity_model = self.env['nh.activity']
        self.activity_data_model = self.env['nh.activity.data']
        self.test_model = self.env['test.activity.data.model0']
        self.test_utils.create_locations()
        self.test_utils.create_users()
        self.test_utils.create_patient()
        spell = self.test_utils.admit_patient()
        activity_one_id = self.test_model.create_activity(
            {
                'parent_id': spell.activity_id.id
            },
            {
                'patient_id': spell.patient_id.id
            }
        )
        self.activity_one = self.activity_model.browse(activity_one_id)
        policy = {
            'cancel_others': True,
            'model': 'test.activity.data.model0',
            'type': 'schedule'
        }
        self.test_model \
            .trigger_policy_activity(self.activity_one, policy, case=1)

        query = [
            ['data_model', '=', 'test.activity.data.model0'],
            ['patient_id', '=', self.test_utils.patient.id],
            ['state', 'not in', ['completed', 'cancelled']]
        ]
        self.activity_two = self.activity_model.search(query)

    def test_cancel_others(self):
        """
        Test that when set to cancel others that the triggering of the policy
        cancels the currently open activities of the same type
        """
        self.assertEqual(self.activity_one.state, 'cancelled')

    def test_schedules_activity(self):
        """
        Test that the activity is then scheduled based on the dictionary sent
        as part of the policy
        """

        self.assertEqual(self.activity_two.state, 'scheduled')

    def test_sets_creator_id(self):
        """
        Test that when the new activity is created that it references the
        passed activity as it's creator
        """
        self.assertEqual(self.activity_two.creator_id.id, self.activity_one.id)
