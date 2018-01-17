from openerp.tests.common import TransactionCase


class TestTriggerPolicy(TransactionCase):
    """
    Test the trigger_policy method on the nh.activity.data model
    """

    def setUp(self):
        """ Set up the tests """
        super(TestTriggerPolicy, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.test_model = self.env['test.activity.data.model0']
        self.test2_model = self.env['test.activity.data.model1']
        self.test3_model = self.env['test.activity.data.model3']
        self.test_utils.admit_and_place_patient()
        self.activity_id = self.test2_model.create_activity(
            {
                'parent_id': self.test_utils.spell.id
            },
            {
                'field1': 'TEST0',
                'patient_id': self.test_utils.patient.id
            }
        )

    def test_no_spell_activity_id(self):
        """
        Test that when there's no spell activity associated with the activity
        for the record that it returns False
        """
        self.assertTrue(False)

    def test_no_activities(self):
        """
        Test that when the policy has no activities that it returns True
        """
        self.assertTrue(False)

    def test_incorrect_case(self):
        """
        Test that when the policy only contains items for a case that isn't
        the one being passed that it doesn't trigger the policy items and
        returns True
        """
        self.assertTrue(False)

    def test_domain_returns_record(self):
        """
        Test that when the call to check if there are existing records returns
        that there are existing records that it doesn't trigger the policy
        items and returns True
        """
        self.assertTrue(False)

    def test_incorrect_policy_context(self):
        """
        Test that when checking the nh.clinical.context of the activity to
        trigger if the contexts don't match then it doesn't trigger the
        policy item and returns True
        """
        self.assertTrue(False)

    def test_mixed_policy_context(self):
        """
        Test that when have a policy definition with two activities, one with
        the correct context and one with another context that it only triggers
        the policy item with the correct context
        """
        self.assertTrue(False)

    def test_triggers_policy(self):
        """
        Test that it creates the activity as defined in the policy+
        """
        self.assertTrue(False)

    def test_05_trigger_policy(self):
        cr, uid = self.cr, self.uid
        activity_id = self.test2_pool.create_activity(cr, uid, {
            'parent_id': self.spell2_id}, {'field1': 'TEST0',
                                           'patient_id': self.patient2_id})
        activity2_id = self.test_pool.create_activity(cr, uid, {
            'parent_id': self.spell2_id}, {'field1': 'TEST1', 'frequency': 30,
                                           'patient_id': self.patient2_id})
        activity3_id = self.test3_pool.create_activity(cr, uid, {
            'parent_id': self.spell2_id}, {'field1': 'TEST2',
                                           'patient_id': self.patient2_id})

        # Scenario 1: Trigger empty policy - does nothing
        self.assertTrue(self.test2_pool.trigger_policy(cr, uid, activity_id),
                        msg="Error triggering policy")

        # Scenario 2:
        # Trigger simple policy. No case. No context. Domains not true
        self.assertTrue(self.test_pool.trigger_policy(cr, uid, activity2_id),
                        msg="Error triggering policy")
        # According to policy, activity 1 and 2 should be cancelled
        # due to cancel_others parameter, activity 3 should still be open.
        self.assertEqual(self.activity_pool.read(
            cr, uid, activity_id, ['state'])['state'], 'cancelled')
        self.assertEqual(self.activity_pool.read(
            cr, uid, activity2_id, ['state'])['state'], 'cancelled')
        self.assertEqual(self.activity_pool.read(
            cr, uid, activity3_id, ['state'])['state'], 'new')
        # The policy should have triggered the creation of 4 new activities,
        # 1 of each data type.
        activity_ids = self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity2_id]])
        self.assertEqual(len(activity_ids), 4)
        self.assertEqual(len(self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity2_id],
                      ['data_model', '=', 'test.activity.data.model0']])), 1)
        self.assertEqual(len(self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity2_id],
                      ['data_model', '=', 'test.activity.data.model1']])), 1)
        self.assertEqual(len(self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity2_id],
                      ['data_model', '=', 'test.activity.data.model3']])), 1)
        self.assertEqual(len(self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity2_id],
                      ['data_model', '=', 'test.activity.data.model4']])), 1)
        for activity in self.activity_pool.browse(cr, uid, activity_ids):
            if activity.data_model == 'test.activity.data.model0':
                # activity should be scheduled,
                # due in 1 hour with initialized values TEST1 and frequency 30
                self.assertEqual(activity.state, 'scheduled')
                self.assertEqual(activity.data_ref.field1, 'TEST1')
                self.assertEqual(activity.data_ref.frequency, 30)
                activity_id = activity.id
            elif activity.data_model == 'test.activity.data.model1':
                # activity should be started with initialized value TEST1
                self.assertEqual(activity.state, 'started')
                self.assertEqual(activity.data_ref.field1, 'TEST1')
            elif activity.data_model == 'test.activity.data.model3':
                # activity should be scheduled,
                # due in 30 minutes with initialized value TEST1
                # and frequency 30
                self.assertEqual(activity.state, 'scheduled')
                self.assertEqual(activity.data_ref.field1, 'TEST1')
                self.assertEqual(activity.data_ref.frequency, 30)
            elif activity.data_model == 'test.activity.data.model4':
                # activity should be completed with
                # initialized value TESTCOMPLETE
                self.assertEqual(activity.state, 'completed')
                self.assertEqual(activity.data_ref.field1, 'TESTCOMPLETE')

        # Scenario 3: Using case to control what to trigger
        self.assertTrue(self.test_pool.trigger_policy(
            cr, uid, activity_id, case=1), msg="Error triggering policy")
        # The policy should have triggered
        # the creation of 1 activity of test.activity.data.model type
        activity_ids = self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity_id]])
        self.assertEqual(len(activity_ids), 1)

        # Scenario 4: Using context and location to control what to trigger
        activity_id = activity_ids[0]
        self.assertTrue(self.test_pool.trigger_policy(
            cr, uid, activity_id, location_id=self.wu_id),
            msg="Error triggering policy")
        # The policy should have triggered the creation of 2 activities
        activity_ids = self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity_id]])
        self.assertEqual(len(activity_ids), 2)
        self.assertEqual(len(self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity2_id],
                      ['data_model', '=', 'test.activity.data.model0']])), 1)
        self.assertEqual(len(self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity2_id],
                      ['data_model', '=', 'test.activity.data.model4']])), 1)
        for activity in self.activity_pool.browse(cr, uid, activity_ids):
            activity_id = activity.id if \
                activity.data_model == 'test.activity.data.model0' \
                else activity_id
        self.assertTrue(self.test_pool.trigger_policy(cr, uid, activity_id,
                                                      location_id=self.wt_id),
                        msg="Error triggering policy")
        # The policy should have triggered the creation of 1 activity
        # of test.activity.data.model type
        activity_ids = self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity_id]])
        self.assertEqual(len(activity_ids), 1)

        # Scenario 5: Using domain to control the activity trigger.
        # The second activity won't be triggered if we have
        # a completed test.activity.data.model type
        activity_id = activity_ids[0]
        self.activity_pool.complete(cr, uid, activity_id)
        self.assertTrue(self.test_pool.trigger_policy(
            cr, uid, activity_id, case=2), msg="Error triggering policy")
        # The policy should have triggered nothing
        activity_ids = self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity_id]])
        self.assertEqual(len(activity_ids), 0)
