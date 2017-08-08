from uuid import uuid4

from openerp.osv.osv import except_orm
from openerp.tests.common import TransactionCase


class TestApiAdmit(TransactionCase):
    """ Test the admit functionality of nh.clinical.api """

    def setUp(self):
        super(TestApiAdmit, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.api_model = self.env['nh.clinical.api']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.registration_model = self.env['nh.clinical.adt.patient.register']
        self.admission_model = self.env['nh.clinical.adt.patient.admit']

        self.test_utils.create_locations()
        self.test_utils.create_users()
        self.test_utils.create_and_register_patient()
        self.hospital_number = self.test_utils.patient.other_identifier
        self.nhs_number = self.test_utils.patient.patient_identifier

    def test_admit_with_hospital_number(self):
        """ Test that we can admit a patient using the hospital number. """
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

    def test_admit_with_nhs_num_patient_already_exists(self):
        """
        Test that we can admit a patient with a record already in the
        system using NHS number.
        """
        already_existing_patient_nhs_number = self.nhs_number
        admit_data = {
            'location': self.test_utils.ward.code,
            'patient_identifier': already_existing_patient_nhs_number
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

    def test_admit_with_nhs_num_patient_does_not_exist(self):
        """
        Test that we cannot admit a patient using NHS number when that
        patient does not already exist.
        """
        new_patient_nhs_number = 'NHS_NUMBER'
        with self.assertRaises(except_orm) as error:
            self.api_model.admit('', {
                'patient_identifier': new_patient_nhs_number
            })
        self.assertEqual(
            error.exception.value,
            'Patient record must have Hospital number.'
        )

    def test_admit_non_existent_patient(self):
        """
        Test that admitting a non-existent patient registers them
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

        patient_search_results = self.patient_model.search([
            ('other_identifier', '=', new_patient_id)
        ])
        self.assertTrue(patient_search_results, msg="Patient was not created.")
        patient = patient_search_results[0]

        registration_search_results = self.registration_model.search([
            ('patient_id', '=', patient.id)
        ])
        self.assertTrue(registration_search_results,
                        msg="Patient registration was not created.")
        registration = registration_search_results[0]

        admission = self.admission_model.search([
            ['registration', '=', registration.id]
        ])[0]
        admission_activity = admission.activity_id
        self.assertTrue(admission_activity, msg="Admit Activity not generated")
        self.assertEqual(admission_activity.state, 'completed')

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
