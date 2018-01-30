from openerp.tests.common import TransactionCase


class TestCheckTriggerDomains(TransactionCase):
    """
    Test that the check_trigger_domains method is returning the correct
    value
    """

    def setUp(self):
        """ Setup the tests """
        super(TestCheckTriggerDomains, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.activity_data_model = self.env['nh.activity.data']
        self.test_utils.admit_and_place_patient()
        self.domain = {
            'object': 'nh.clinical.patient.placement',
            'domain': [['state', 'in', ['cancelled', 'completed']]]
        }

    def test_no_domains(self):
        """
        Test that if no domains are passed that it returns False
        """
        result = self.activity_data_model.check_trigger_domains(
            self.test_utils.spell_activity
        )
        self.assertFalse(result)

    def test_records_found(self):
        """
        Test that if the domain returns records then it returns True
        """
        result = self.activity_data_model.check_trigger_domains(
            self.test_utils.spell_activity,
            [
                {
                    'object': 'nh.activity',
                    'domain': [
                        ['data_model', '=', 'nh.clinical.patient.admission'],
                        ['state', 'in', ['cancelled', 'completed']]
                    ]
                }
            ]
        )
        self.assertTrue(result)

    def test_no_records_found(self):
        """
        Test that if the domains returns no records then it returns False
        """
        result = self.activity_data_model.check_trigger_domains(
            self.test_utils.spell_activity,
            [
                {
                    'object': 'nh.activity',
                    'domain': [
                        ['data_model', '=', 'nh.clinical.patient.placement'],
                        ['state', '=', 'new']
                    ]
                }
            ]
        )
        self.assertFalse(result)
