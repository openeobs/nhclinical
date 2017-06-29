from openerp.tests.common import TransactionCase
from openerp.osv.osv import except_orm
from uuid import uuid4


class TestApiTransfer(TransactionCase):
    """ Test the transfer method of nh.clinical.api """

    def setUp(self):
        super(TestApiTransfer, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.api_model = self.env['nh.clinical.api']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.admit_and_place_patient()
        self.hospital_number = self.test_utils.patient.other_identifier
        self.nhs_number = self.test_utils.patient.patient_identifier

    def test_transfer_with_hosp_num(self):
        """ Test we can transfer a patient using their hospital number """
        transfer_data = {
            'location': self.test_utils.other_ward.code
        }
        self.api_model.transfer(self.hospital_number, transfer_data)
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.patient.transfer'],
                ['patient_id', '=', self.test_utils.patient.id]
            ]
        )
        self.assertTrue(activity, msg="Transfer Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_transfer_with_nhs_num(self):
        """ Test we can transfer a patient using their nhs number """
        # Scenario 2: Update admission using NHS Number
        transfer_data = {
            'location': self.test_utils.other_ward.code,
            'patient_identifier': self.nhs_number
        }
        self.api_model.transfer('', transfer_data)
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.patient.transfer'],
                ['patient_id', '=', self.test_utils.patient.id]
            ]
        )
        self.assertTrue(activity, msg="Transfer Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_transfer_non_existent_patient(self):
        """ Test we can transfer a non-existent patient """
        new_patient_id = str(uuid4())
        transfer_data = {
            'original_location': self.test_utils.ward.code,
            'location': self.test_utils.other_ward.code,
            'patient_identifier': new_patient_id,
            'family_name': "Fname9000",
            'given_name': 'Gname9000',
            'dob': '1988-08-14 18:00:00',
            'gender': 'F',
            'sex': 'F'
        }
        self.api_model.transfer(new_patient_id, transfer_data)
        patient = self.patient_model.search(
            [
                ('other_identifier', '=', new_patient_id)
            ]
        )
        self.assertTrue(patient, msg="Patient was not created")
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.patient.transfer'],
                ['patient_id', '=', patient.id]
            ]
        )
        self.assertTrue(activity, msg="Transfer Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_raises_no_patient_info(self):
        """
        Test that exception is raised trying to call method with no patient
        information
        """
        with self.assertRaises(except_orm) as error:
            self.api_model.transfer('', {})
        self.assertEqual(
            error.exception.value,
            'Patient\'s NHS or Hospital numbers must be provided'
        )
