from openerp.tests.common import TransactionCase
from uuid import uuid4


class TestApiRegister(TransactionCase):
    """ Test the nh.clinical.api register method that Registers a patient """

    def setUp(self):
        super(TestApiRegister, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.api_model = self.env['nh.clinical.api']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.create_locations()
        self.patient_identifier = str(uuid4())[:6]

    def test_register_patient_with_hos_num(self):
        """ Test we can register a patient with hospital number """

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

    def test_register_patient_with_nhs_num(self):
        """ Test that we can register a patient with an NHS number """
        patient_data = {
            'patient_identifier': self.patient_identifier,
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
