from openerp.tests.common import TransactionCase


class TestTriggerPolicyChangeState(TransactionCase):
    """
    Test that the trigger_policy_change_state method changes the state of the
    supplied activity based on the policy dictionary passed
    """

    def setUp(self):
        """ Set up the tests """
        super(TestTriggerPolicyChangeState, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        activity_model = self.env['nh.activity']
        self.activity_data_model = self.env['nh.activity.data']
        test_model = self.env['test.activity.data.model0']
        self.test_utils.admit_and_place_patient()
        self.test_activity_id = test_model.create_activity(
            {
                'parent_id': self.test_utils.spell.activity_id.id
            },
            {
                'patient_id': self.test_utils.patient.id
            }
        )
        self.test_activity = activity_model.browse(self.test_activity_id)

    def test_schedules_activity(self):
        """
        Test that when no type is set that the triggered activity is scheduled
        for an hours time
        """
        self.activity_data_model.trigger_policy_change_state(
            self.test_activity_id, {})
        self.assertEqual(self.test_activity.state, 'scheduled')

    def test_schedules_recurring_activity(self):
        """
        Test that when the type is set to recurring that the triggered
        activity is scheduled with the recurrence configuration for that
        activity
        """
        self.activity_data_model.trigger_policy_change_state(
            self.test_activity_id,
            {
                'type': 'recurring'
            }
        )
        self.assertEqual(self.test_activity.state, 'scheduled')

    def test_starts_activity(self):
        """
        Test that when the type is set to start that the triggered activity
        is started
        """
        self.activity_data_model.trigger_policy_change_state(
            self.test_activity_id,
            {
                'type': 'start'
            }
        )
        self.assertEqual(self.test_activity.state, 'started')

    def test_completes_activity(self):
        """
        Test that when the type is set to complete that the triggered activity
        is completed
        """
        self.activity_data_model.trigger_policy_change_state(
            self.test_activity_id,
            {
                'type': 'complete'
            }
        )
        self.assertEqual(self.test_activity.state, 'completed')

    def test_completes_activity_with_data(self):
        """
        Test that when the type is set to complete and data is also passed that
        the triggered activity has that data submitted against it and it is
        then completed
        """
        self.activity_data_model.trigger_policy_change_state(
            self.test_activity_id,
            {
                'type': 'complete',
                'data': {
                    'field1': 'Test'
                }
            }
        )
        self.assertEqual(self.test_activity.state, 'completed')
        self.assertEqual(self.test_activity.data_ref.field1, 'Test')
