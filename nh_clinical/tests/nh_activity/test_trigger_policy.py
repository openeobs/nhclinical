from openerp.tests.common import TransactionCase


class TestTriggerPolicy(TransactionCase):
    """
    Test the trigger_policy method on the nh.activity.data model
    """

    def setUp(self):
        """ Set up the tests """
        super(TestTriggerPolicy, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.activity_model = self.env['nh.activity']
        self.test1_model = self.env['test.activity.data.model0']
        self.test2_model = self.env['test.activity.data.model1']
        self.test3_model = self.env['test.activity.data.model3']
        self.test_utils.admit_and_place_patient()
        self.test_1_activity_id = self.test1_model.create_activity(
            {
                'parent_id': self.test_utils.spell.activity_id.id
            },
            {
                'field1': 'TEST',
                'frequency': 10,
                'patient_id': self.test_utils.patient.id
            }
        )
        self.test_1_activity = self.activity_model.browse(
            self.test_1_activity_id)
        self.test_2_activity_id = self.test2_model.create_activity(
            {
                'parent_id': self.test_utils.spell.id
            },
            {
                'field1': 'TEST',
                'patient_id': self.test_utils.patient.id
            }
        )
        self.test_3_activity_id = self.test3_model.create_activity(
            {
                'parent_id': self.test_utils.spell.id
            },
            {
                'field1': 'TEST',
                'frequency': 10,
                'patient_id': self.test_utils.patient.id
            }
        )

    def test_no_spell_activity_id(self):
        """
        Test that when there's no spell activity associated with the activity
        for the record that it returns False
        """
        orphaned_activity = self.test2_model.create_activity({}, {})
        result = self.test2_model.trigger_policy(
            orphaned_activity
        )
        self.assertFalse(result)

    def test_no_activities(self):
        """
        Test that when the policy has no activities that it returns True
        """
        result = self.test2_model.trigger_policy(
            self.test_2_activity_id
        )
        self.assertTrue(result)

    def test_incorrect_case(self):
        """
        Test that when the policy only contains items for a case that isn't
        the one being passed that it doesn't trigger the policy items and
        returns True
        """
        result = self.test1_model.trigger_policy(
            self.test_1_activity_id,
            case=666
        )
        self.assertTrue(result)

    def test_domain_returns_record(self):
        """
        Test that when the call to check if there are existing records returns
        that there are existing records that it doesn't trigger the policy
        items and returns True
        """
        self.test_1_activity.complete()
        result = self.test1_model.trigger_policy(
            self.test_1_activity_id,
            case=2
        )
        self.assertTrue(result)

    def test_incorrect_policy_context(self):
        """
        Test that when checking the nh.clinical.context of the activity to
        trigger if the contexts don't match then it doesn't trigger the
        policy item and returns True
        """
        result = self.test1_model.trigger_policy(
            self.test_1_activity_id,
            location_id=self.test_utils.bed.id,
            case=3
        )
        self.assertTrue(result)

    def test_mixed_policy_context(self):
        """
        Test that when have a policy definition with two activities, one with
        the correct context and one with another context that it only triggers
        the policy item with the correct context
        """
        context_model = self.env['nh.clinical.context']
        new_context = context_model.create(
            {
                'name': 'test',
                'models': ['nh.clinical.location']
            }
        )
        self.test_utils.bed.context_ids = [[6, 0, new_context.ids]]
        query = [
            ['data_model', '=', 'test.activity.data.model3'],
            ['state', '=', 'scheduled'],
            ['creator_id', '=', self.test_1_activity_id]
        ]
        before = self.activity_model.search_count(query)
        self.test1_model.trigger_policy(
            self.test_1_activity_id,
            location_id=self.test_utils.bed.id,
            case=5
        )
        after = self.activity_model.search_count(query)
        self.assertEqual(after, before+1)

    def test_triggers_policy(self):
        """
        Test that it creates the activity as defined in the policy
        """
        self.test1_model.trigger_policy(
            self.test_1_activity_id,
            case=1
        )
        self.assertEqual(self.test_1_activity.state, 'cancelled')
        activities = self.activity_model.search(
            [
                ['data_model', '=', 'test.activity.data.model0'],
                ['state', '=', 'scheduled'],
                ['creator_id', '=', self.test_1_activity_id]
            ]
        )
        self.assertTrue(activities)
