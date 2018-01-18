from openerp.tests.common import TransactionCase


class TestTriggerPolicyCreateActivity(TransactionCase):
    """
    Test that the trigger_policy_create_activity method on nh.clinical.data
    creates an activity with the relevant
    """

    def setUp(self):
        """ Set up the tests """
        super(TestTriggerPolicyCreateActivity, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.activity_model = self.env['nh.activity']
        self.test_policy_model = self.env['test.activity.data.model0']
        self.test_no_policy_model = self.env['test.activity.data.model3']
        self.test_utils.admit_and_place_patient()
        self.spell_activity = self.test_utils.spell_activity

    def test_creates_new_activity(self):
        """
        Test that it creates an activity for the defined model with no case
        defined
        """
        model_instance = self.test_no_policy_model.create({})
        new_act_id = model_instance.trigger_policy_create_activity(
            self.spell_activity,
            self.test_no_policy_model
        )
        new_act = self.activity_model.browse(new_act_id)
        self.assertEqual(new_act.spell_activity_id.id, self.spell_activity.id)

    def test_create_activity_with_data(self):
        """
        Test that where a model implements the _get_policy_create_data() method
        that is adds this data to the activity
        """
        policy_instance = self.test_policy_model.create({
            'field1': 'Test',
            'frequency': 1
        })
        new_act_id = policy_instance.trigger_policy_create_activity(
            self.spell_activity,
            self.test_policy_model,
            1
        )
        new_act = self.activity_model.browse(new_act_id)
        self.assertEqual(new_act.data_ref.field1, 'Test')
        self.assertEqual(new_act.data_ref.frequency, 1)
        self.assertEqual(new_act.spell_activity_id.id, self.spell_activity.id)
