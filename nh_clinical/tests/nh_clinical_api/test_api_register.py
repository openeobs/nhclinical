from uuid import uuid4

from openerp.tests.common import TransactionCase


class TestApiRegister(TransactionCase):
    """ Test the nh.clinical.api register method that Registers a patient """

    def setUp(self):
        super(TestApiRegister, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.api_model = self.env['nh.clinical.api']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.registration_model = self.env['nh.clinical.adt.patient.register']

        self.test_utils.create_locations()
        self.patient_identifier = str(uuid4())[:6]

    def test_register_patient_with_hos_num(self):
        """ Test we can register a patient with hospital number. """

        patient_data = {
            'family_name': "Fname",
            'given_name': 'Gname',
            'dob': '1988-08-14 18:00:00',
            'gender': 'M',
            'sex': 'M'
        }

        self.api_model.register(self.patient_identifier, patient_data)

        patient = self.patient_model.search(
            [
                ('other_identifier', '=', self.patient_identifier)
            ]
        )
        self.assertTrue(patient, msg="Patient was not created")
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.patient.register'],
                ['patient_id', '=', patient.id]
            ]
        )
        self.assertTrue(activity, msg="Register Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_register_patient_with_hos_num_in_vals_dict(self):
        """
        Test that we can register a patient with a hospital number in the
        values dictionary instead of in as a positional argument.
        """
        patient_data = {
            'patient_identifier': self.patient_identifier,
            'other_identifier': self.patient_identifier,
            'family_name': "Fname2",
            'given_name': 'Gname2',
            'gender': 'F',
            'sex': 'F'
        }
        self.api_model.register('', patient_data)
        patient = self.patient_model.search(
            [
                ('patient_identifier', '=', self.patient_identifier)
            ]
        )
        self.assertTrue(patient, msg="Patient was not created")
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.patient.register'],
                ['patient_id', '=', patient.id]
            ]
        )
        self.assertTrue(activity, msg="Register Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_returns_register_id(self):
        """
        Used to return patient ID. Assert that the ID of the register record
        (not the activity) is returned.
        """
        patient_data = {
            'family_name': "Fname",
            'given_name': 'Gname',
            'dob': '1988-08-14 18:00:00',
            'gender': 'M',
            'sex': 'M'
        }
        registration_id = self.api_model.register(
            self.patient_identifier, patient_data)

        # Test register ID by using it to lookup details about the patient.
        registration = self.registration_model.browse(registration_id)
        self.assertEqual(patient_data['dob'], registration.patient_id.dob)
        self.assertEqual(
            patient_data['family_name'], registration.patient_id.family_name)
