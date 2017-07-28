from openerp.tests.common import TransactionCase
from openerp.osv.osv import except_orm
from uuid import uuid4


class TestApiAdmit(TransactionCase):
    """ Test the admit functionality of nh.clinical.api """

    def setUp(self):
        super(TestApiAdmit, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.api_model = self.env['nh.clinical.api']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.create_locations()
        self.test_utils.create_users()
        self.test_utils.create_patient()
        self.hospital_number = self.test_utils.patient.other_identifier
        self.nhs_number = self.test_utils.patient.patient_identifier

    def test_admit_with_hosp_num(self):
        """ Test that we can admit a patient using the hospital number """
        admit_data = {
            'location': self.test_utils.ward.code
        }
        self.api_model.admit(self.hospital_number, admit_data)
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.patient.admit'],
                ['patient_id', '=', self.test_utils.patient.id]
            ]
        )
        self.assertTrue(activity, msg="Admit Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_admit_with_nhs_num(self):
        """ Test that we can admit a patient using NHS number """
        admit_data = {
            'location': self.test_utils.ward.code,
            'patient_identifier': self.nhs_number
        }
        self.api_model.admit('', admit_data)
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.patient.admit'],
                ['patient_id', '=', self.test_utils.patient.id]
            ]
        )
        self.assertTrue(activity, msg="Admit Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_admit_non_existant_patient(self):
        """
        Test that admitting a non-existant patient registers them
        """
        new_patient_id = str(uuid4()).replace('-', '')
        admit_data = {
            'location': self.test_utils.ward.code,
            'patient_identifier': new_patient_id,
            'family_name': "Fname400",
            'given_name': 'Gname400',
            'dob': '1988-08-14 18:00:00',
            'gender': 'M',
            'sex': 'M'
        }

        self.api_model.admit(new_patient_id, admit_data)

        patient = self.patient_model.search(
            [
                ('other_identifier', '=', new_patient_id)
            ]
        )
        self.assertTrue(patient, msg="Patient was not created")
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.patient.admit'],
                ['patient_id', '=', patient.id]
            ]
        )
        self.assertTrue(activity, msg="Admit Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_raises_no_patient_info(self):
        """
        Test that exception is raised trying to call method with no patient
        information
        """
        with self.assertRaises(except_orm) as error:
            self.api_model.admit('', {})
        self.assertEqual(
            error.exception.value,
            'Patient\'s NHS or Hospital numbers must be provided'
        )
