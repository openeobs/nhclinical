from openerp.tests.common import TransactionCase
from openerp.osv.osv import except_orm
from uuid import uuid4


class TestApiAdmitUpdate(TransactionCase):
    """ Test the admit_update method of nh.clinical.api """

    def setUp(self):
        super(TestApiAdmitUpdate, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.api_model = self.env['nh.clinical.api']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.admit_and_place_patient()
        self.hospital_number = self.test_utils.patient.other_identifier
        self.nhs_number = self.test_utils.patient.patient_identifier

    def test_update_admit_with_hosp_num(self):
        """ Test can update admission with Hospital Number """
        update_data = {
            'location': self.test_utils.other_ward.code
        }

        self.api_model.admit_update(self.hospital_number, update_data)
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.spell.update'],
                ['patient_id', '=', self.test_utils.patient.id]
            ]
        )
        self.assertTrue(activity, msg="Spell Update Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_update_admit_with_nhs_num(self):
        """ Test can update admission with NHS Number """
        update_data = {
            'location': self.test_utils.other_ward.code,
            'patient_identifier': self.nhs_number
        }

        self.api_model.admit_update('', update_data)
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.spell.update'],
                ['patient_id', '=', self.test_utils.patient.id]
            ]
        )
        self.assertTrue(activity, msg="Spell Update Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_raises_on_updating_non_existent_patient(self):
        """
        Test that an exception is raised attempting to update the admission of
        a patient that does exist
        """
        update_data = {
            'location': "WARD0",
            'patient_identifier': 'TESTNHS005',
            'family_name': "Fname5000",
            'given_name': 'Gname5000',
            'dob': '1988-08-14 18:00:00',
            'gender': 'F',
            'sex': 'F'
        }

        with self.assertRaises(except_orm) as error:
            self.api_model.admit_update(str(uuid4()), update_data)
        self.assertEqual(
            error.exception.value,
            'The patient does not have an open spell!'
        )

    def test_raises_no_patient_info(self):
        """
        Test that exception is raised trying to call method with no patient
        information
        """
        with self.assertRaises(except_orm) as error:
            self.api_model.admit_update('', {})
        self.assertEqual(
            error.exception.value,
            'Patient\'s NHS or Hospital numbers must be provided'
        )
