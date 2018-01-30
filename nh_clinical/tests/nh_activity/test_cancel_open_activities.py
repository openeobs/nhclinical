from openerp.tests.common import TransactionCase


class TestCancelOpenActivities(TransactionCase):
    """
    Test that the cancel_open_activities() method is working correctly
    """

    def setUp(self):
        """
        Set up the tests
        """
        super(TestCancelOpenActivities, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.activity_model = self.env['nh.activity']
        self.test_model = self.env['test.activity.data.model1']
        self.test_utils.create_locations()
        self.test_utils.create_users()
        self.test_utils.create_patient()
        self.spell = self.test_utils.admit_patient()
        activity_id = self.test_utils.create_placement()
        self.activity = self.activity_model.browse(activity_id)

    def test_cancels_open_activities(self):
        """
        Test that when provided with the spell's activity ID that it cancels
        the open activities associated with that spell
        """
        self.assertTrue(self.activity_model.cancel_open_activities(
            self.spell.activity_id.id,
            'nh.clinical.patient.placement'
        ))
        self.assertEqual(self.activity.state, 'cancelled')
