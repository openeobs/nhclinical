# -*- coding: utf-8 -*-
from openerp.exceptions import ValidationError
from openerp.tests.common import TransactionCase
from openerp.tools.misc import mute_logger
from psycopg2 import IntegrityError


class TestAdtPatientRegister(TransactionCase):
    """
    Test the nh.clinical.adt.patient.register - Patient Registration via
    ADT model.
    """
    valid_register_data = {
        'family_name': 'Family',
        'middle_names': 'Middle',
        'given_name': 'Given',
        'other_identifier': 'TEST001',
        'dob': '1984-10-01 00:00:00',
        'gender': 'M',
        'sex': 'M'
    }

    def setUp(self):
        super(TestAdtPatientRegister, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.register_model = self.env['nh.clinical.adt.patient.register']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.create_locations()

    def _create_register_activity_and_submit(self, register_data):
        register_activity_id = self.register_model.create_activity({}, {})
        register_activity = self.activity_model.browse(register_activity_id)
        register_activity.submit(register_data)
        return register_activity

    def test_register_new_hospital_number(self):
        """ Test registering a new patient with hospital number. """
        register_activity = self._create_register_activity_and_submit(
            self.valid_register_data)
        patient_id = register_activity.complete()
        patient = self.patient_model.browse(patient_id)
        self.assertTrue(
            patient,
            msg="Patient Register: patient id not returned")
        self.assertEqual(
            self.valid_register_data['family_name'],
            patient.family_name,
            msg="Patient Register: wrong patient data registered")
        self.assertEqual(
            self.valid_register_data['given_name'],
            patient.given_name,
            msg="Patient Register: wrong patient data registered")
        self.assertEqual(
            self.valid_register_data['other_identifier'],
            patient.other_identifier,
            msg="Patient Register: wrong patient data registered")
        self.assertEqual(
            self.valid_register_data['dob'],
            patient.dob,
            msg="Patient Register: wrong patient data registered")
        self.assertEqual(
            self.valid_register_data['gender'],
            patient.gender,
            msg="Patient Register: wrong patient data registered")
        self.assertEqual(
            self.valid_register_data['sex'],
            patient.sex,
            msg="Patient Register: wrong patient data registered")

    def test_register_new_patient_with_hospital_number_in_values_dict(self):
        """
        Register a new patient with hospital number in the values dictionary
        rather than passed as a positional argument.
        """
        register_data = {
            'family_name': 'Family',
            'given_name': 'Given',
            'patient_identifier': 'TEST001',
            'other_identifier': 'TEST0001',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }
        register_activity = self._create_register_activity_and_submit(
            register_data)
        patient_id = register_activity.complete()
        self.assertTrue(patient_id,
                        msg="Patient Register: patient id not returned")

    def test_register_no_hospital_number(self):
        """
        Test raises an error when submitting data for incorrect activity.
        """
        register_data = {
            'family_name': 'Family',
            'given_name': 'Given',
            'patient_identifier': 'TEST001',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }
        with self.assertRaises(ValidationError) as error:
            self._create_register_activity_and_submit(register_data)
        self.assertEqual(
            error.exception.value,
            'Patient record must have Hospital number.'
        )

    def test_register_no_names(self):
        """
        Test raises an error when submitting data for incorrect activity.
        """
        register_data = {
            'dob': '1984-10-01 00:00:00',
            'other_identifier': 'TEST001',
            'gender': 'M',
            'sex': 'M'
        }
        with self.assertRaises(ValidationError) as error:
            self._create_register_activity_and_submit(register_data)
        self.assertEqual(
            error.exception.value,
            'Patient record must have valid Given and Family Names'
        )

    @mute_logger('openerp.sql_db')
    def test_register_duplicate_nhs_number(self):
        """
        Test raises an error when submitting duplicate NHS Number.
        """
        register_data = {
            'family_name': 'Family',
            'given_name': 'Given',
            'patient_identifier': 'TEST001',
            'other_identifier': 'TEST0001',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }
        register_activity = self._create_register_activity_and_submit(
            register_data)
        register_activity.complete()

        with self.assertRaises(IntegrityError) as error:
            new_register_activity = self._create_register_activity_and_submit(
                register_data)
            new_register_activity.complete()
        self.assertTrue(
            'duplicate key value violates unique constraint' in
            error.exception.message
        )

    @mute_logger('openerp.sql_db')
    def test_register_duplicate_hospital_number(self):
        """
        Test raises an error when submitting duplicate NHS Number.
        """
        register_data = {
            'family_name': 'Family',
            'given_name': 'Given',
            'other_identifier': 'TEST001',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }
        register_activity = self._create_register_activity_and_submit(
            register_data)
        register_activity.complete()

        with self.assertRaises(IntegrityError) as error:
            new_register_activity = self._create_register_activity_and_submit(
                register_data)
            new_register_activity.complete()
        self.assertTrue(
            'duplicate key value violates unique constraint' in
            error.exception.message
        )

    def test_patient_created_on_complete(self):
        """
        A register record can be created with details of the patient but the
        patient record itself is not actually created until completion of the
        registration activity. When it is created it uses the data already
        created on the registration such as names and identifiers.
        """
        register_activity = self._create_register_activity_and_submit(
            self.valid_register_data)

        patient_model = self.env['nh.clinical.patient']
        patient_search_results_before = patient_model.search([(
            'other_identifier',
            '=',
            self.valid_register_data['other_identifier']
        )])
        self.assertFalse(patient_search_results_before)

        register_activity.complete()

        patient_search_results_after = patient_model.search([(
            'other_identifier',
            '=',
            self.valid_register_data['other_identifier']
        )])
        self.assertTrue(patient_search_results_after)

    def test_name_field_value_is_patient_full_name(self):
        """
        The 'name' field is used in the UI for various elements. When viewing
        the register data we want to see the name of the patient the register
        concerns.
        """
        register_activity = self._create_register_activity_and_submit(
            self.valid_register_data)
        expected = 'Family, Given Middle'
        actual = register_activity.data_ref.display_name
        self.assertEqual(expected, actual)
