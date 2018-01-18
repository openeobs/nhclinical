from openerp.tests.common import TransactionCase


class TestTriggerPolicyCancelOthers(TransactionCase):
    """
    Test that the trigger_policy_cancel others method works as intended
    """

    def setUp(self):
        """ Set up the tests """
        super(TestTriggerPolicyCancelOthers, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.activity_model= self.env['nh.activity']
        self.placement_model = self.env['nh.clinical.patient.placement']
        self.admission_model = self.env['nh.clinical.patient.admission']
        self.test_utils.create_locations()
        self.test_utils.create_users()
        self.test_utils.create_patient()
        spell = self.test_utils.admit_patient()
        self.test_utils.create_placement()
        self.spell_activity_id = spell.activity_id.id

    def test_cancels_activities(self):
        """
        Test that when calling trigger_policy_cancel_others() that it cancels
        the activities on the passed model
        """
        query = [
            ['data_model', '=', 'nh.clinical.patient.placement'],
            ['patient_id', '=', self.test_utils.patient.id],
            ['state', 'not in', ['completed', 'cancelled']]
        ]
        before = self.activity_model.search_count(query)
        self.placement_model\
            .trigger_policy_cancel_others(
                self.spell_activity_id, 'nh.clinical.patient.placement')
        after = self.activity_model.search_count(query)
        self.assertLess(after, before)

    def test_placement_cancel_reason(self):
        """
        Test that when calling trigger_policy_cancel_others() on
        nh.clinical.patient.placement model that it cancels the activity with
        the cancel reason of 'cancelled by placement'
        """
        self.placement_model \
            .trigger_policy_cancel_others(
                self.spell_activity_id, 'nh.clinical.patient.placement')
        query = [
            ['data_model', '=', 'nh.clinical.patient.placement'],
            ['patient_id', '=', self.test_utils.patient.id],
            ['state', '=', 'cancelled']
        ]
        result = self.activity_model.search(query)
        self.assertEqual(result.cancel_reason_id.name, 'Placement')

    def test_non_placement_cancel_reason(self):
        """
        Test that when calling trigger_policy_cancel_others() on a model other
        than nh.clinical.patient.placement that it cancels the activity without
        defining a reason
        """
        self.admission_model \
            .trigger_policy_cancel_others(
                self.spell_activity_id, 'nh.clinical.patient.placement')
        query = [
            ['data_model', '=', 'nh.clinical.patient.placement'],
            ['patient_id', '=', self.test_utils.patient.id],
            ['state', '=', 'cancelled']
        ]
        result = self.activity_model.search(query)
        self.assertFalse(result.cancel_reason_id.id)
