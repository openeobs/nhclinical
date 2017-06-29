from openerp.tests.common import TransactionCase
from openerp.osv.osv import except_orm
from uuid import uuid4


class TestApiUpdate(TransactionCase):
    """ Test the update method of nh.clinical.api """

    def setUp(self):
        super(TestApiUpdate, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.api_model = self.env['nh.clinical.api']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.admit_and_place_patient()
        self.hospital_number = self.test_utils.patient.other_identifier
        self.nhs_number = self.test_utils.patient.patient_identifier

    def test_update_with_hos_num(self):
        """ Test can update patient using hospital number """
        patient_data = {
            'family_name': "Fname0",
            'given_name': 'Gname0',
            'dob': '1988-08-14 18:00:00',
            'gender': 'M',
            'sex': 'M'
        }

        self.api_model.update(self.hospital_number, patient_data)
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.patient.update'],
                ['patient_id', '=', self.test_utils.patient.id]
            ]
        )
        self.assertTrue(activity, msg="Update Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_update_with_nhs_number(self):
        """ Test can update patient using NHS number """
        patient_data = {
            'patient_identifier': self.nhs_number,
            'family_name': "Fname20",
            'given_name': 'Gname20',
            'dob': '1988-08-14 18:00:00',
            'gender': 'F',
            'sex': 'F'
        }

        self.api_model.update('', patient_data)
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.patient.update'],
                ['patient_id', '=', self.test_utils.patient.id]
            ]
        )
        self.assertTrue(activity.id, msg="Update Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_registers_no_existant_patient(self):
        """
        Test that on trying up update a patient that does not exist it instead
        registers that patient
        """
        new_patient_id = str(uuid4())
        patient_data = {
            'patient_identifier': new_patient_id,
            'family_name': "Fname30",
            'given_name': 'Gname30',
            'dob': '1988-08-14 18:00:00',
            'gender': 'M',
            'sex': 'M'
        }

        self.api_model.update(new_patient_id, patient_data)

        patient = self.patient_model.search(
            [
                ('other_identifier', '=', new_patient_id)
            ]
        )
        self.assertTrue(patient, msg="Patient was not created")
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.patient.update'],
                ['patient_id', '=', patient.id]
            ]
        )
        self.assertTrue(activity, msg="Update Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_raises_no_patient_info(self):
        """
        Test that exception is raised trying to call method with no patient
        information
        """
        with self.assertRaises(except_orm) as error:
            self.api_model.update('', {})
        self.assertEqual(
            error.exception.value,
            'Patient\'s NHS or Hospital numbers must be provided'
        )
