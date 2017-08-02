from openerp.tests.common import TransactionCase
from openerp.osv.osv import except_orm


class TestApiCancelDischarge(TransactionCase):
    """ Test the cancel_discharge method of nh.clinical.api """

    def setUp(self):
        super(TestApiCancelDischarge, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.api_model = self.env['nh.clinical.api']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.admit_and_place_patient()
        self.hospital_number = self.test_utils.patient.other_identifier
        self.nhs_number = self.test_utils.patient.patient_identifier
        self.test_utils.discharge_patient()

    def test_cancel_discharge(self):
        """ Test that we can cancel a discharge """
        # Scenario 1: Cancel a discharge
        self.api_model.cancel_discharge(self.hospital_number)
        activity = self.activity_model.search(
            [
                [
                    'data_model',
                    '=',
                    'nh.clinical.adt.patient.cancel_discharge'
                ],
                ['patient_id', '=', self.test_utils.patient.id]
            ]
        )
        self.assertTrue(
            activity, msg="Cancel Discharge Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_raises_on_no_patient_info(self):
        """ Test that an exception is raised if no patient info is passed """
        with self.assertRaises(except_orm) as error:
            self.api_model.cancel_discharge('')
        self.assertEqual(
            error.exception.value,
            'Patient\'s NHS or Hospital numbers must be provided'
        )
