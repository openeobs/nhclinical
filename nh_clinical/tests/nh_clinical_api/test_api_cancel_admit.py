from openerp.tests.common import TransactionCase
from openerp.osv.osv import except_orm
from uuid import uuid4


class TestApiCancelAdmit(TransactionCase):
    """ Test the cancel_admit method of nh.clinical.api """

    def setUp(self):
        super(TestApiCancelAdmit, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.api_model = self.env['nh.clinical.api']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.admit_and_place_patient()
        self.hospital_number = self.test_utils.patient.other_identifier
        self.nhs_number = self.test_utils.patient.patient_identifier

    def test_cancel_admission(self):
        """ TEst that we can cancel an admission """
        self.api_model.cancel_admit(self.hospital_number)
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.patient.cancel_admit'],
                ['patient_id', '=', self.test_utils.patient.id]
            ]
        )
        self.assertTrue(activity,
                        msg="Cancel Admission Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_raises_cancel_admission_non_existent_patient(self):
        """
        Test that an exception is raised when trying to cancel admission for a
        patient that does not exist
        """
        with self.assertRaises(except_orm) as error:
            self.api_model.cancel_admit(uuid4())
        self.assertEqual(
            error.exception.value,
            'There is no patient in system with credentials provided'
        )
