from openerp.tests.common import TransactionCase
from openerp.osv.osv import except_orm
from uuid import uuid4


class TestApiDischarge(TransactionCase):
    """ Test the discharge method of nh.clinical.api """

    def setUp(self):
        super(TestApiDischarge, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.api_model = self.env['nh.clinical.api']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.admit_and_place_patient()
        self.hospital_number = self.test_utils.patient.other_identifier
        self.nhs_number = self.test_utils.patient.patient_identifier

    def test_discharge_with_hosp_num(self):
        """ Test we can discharge a patient using their hospital number """
        discharge_data = {
            'location': 'U'
        }
        self.api_model.discharge(self.hospital_number, discharge_data)
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.patient.discharge'],
                ['patient_id', '=', self.test_utils.patient.id]
            ]
        )
        self.assertTrue(activity, msg="Discharge Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_discharge_with_nhs_num(self):
        """ Test can discharge a patient using their nhs number """
        discharge_data = {
            'patient_identifier': self.nhs_number,
            'location': 'U'
        }

        self.api_model.discharge('', discharge_data)
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.patient.discharge'],
                ['patient_id', '=', self.test_utils.patient.id]
            ]
        )
        self.assertTrue(activity, msg="Discharge Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_discharge_non_existent_patient_creates_them(self):
        """
        Test that when discharging a non-existent patient we create them
        """
        new_patient_id = str(uuid4()).replace('-', '')
        discharge_data = {
            'location': self.test_utils.ward.code,
            'given_name': 'Test',
            'family_name': 'McTesterson'
        }

        self.api_model.discharge(new_patient_id, discharge_data)

        patient = self.patient_model.search(
            [
                ('other_identifier', '=', new_patient_id)
            ]
        )
        self.assertTrue(patient, msg="Patient was not created")
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.patient.discharge'],
                ['patient_id', '=', patient.id]
            ]
        )
        self.assertTrue(activity, msg="Discharge Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_raises_no_patient_info(self):
        """
        Test that exception is raised trying to call method with no patient
        information
        """
        with self.assertRaises(except_orm) as error:
            self.api_model.discharge('', {})
        self.assertEqual(
            error.exception.value,
            'Patient\'s NHS or Hospital numbers must be provided'
        )
