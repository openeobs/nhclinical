from openerp.tests.common import TransactionCase
from openerp.osv.osv import except_orm
from openerp.tools.misc import mute_logger
from psycopg2 import IntegrityError
from uuid import uuid4


class TestUniqueIdentifierConstraint(TransactionCase):
    """
    Test that the Hospital and NHS Numbers are unique and a user cannot
    create another patient with duplicate NHS/Hospital numbers
    """

    def setUp(self):
        super(TestUniqueIdentifierConstraint, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.create_locations()
        self.test_utils.create_users()
        self.test_utils.create_patient()
        self.existing_hospital_number = \
            self.test_utils.patient.other_identifier
        self.existing_nhs_number = self.test_utils.patient.patient_identifier
        self.patient_data = {
            'family_name': 'Family',
            'given_name': 'Given',
            'middle_names': 'Middle Names',
            'dob': '2000-01-01 00:00:00',
            'sex': 'U',
            'gender': 'U',
            'ethnicity': 'Z'
        }

    def test_raises_create_no_identifiers(self):
        """
        Test that an exception is raised if patient is created without
        identifiers
        """
        with self.assertRaises(except_orm) as error:
            self.patient_model.create(self.patient_data)
        self.assertEqual(
            error.exception.value,
            'Patient record must have Hospital number'
        )

    @mute_logger('openerp.sql_db')
    def test_raises_on_create_duplicate_hosp_num(self):
        """
        Test that an exception is raised if patient is create with same
        hospital number as another patient
        """
        vals = self.patient_data.copy()
        vals.update(
            {
                'other_identifier': self.existing_hospital_number
            }
        )
        with self.assertRaises(IntegrityError) as error:
            self.patient_model.create(vals)
        self.assertTrue(
            'duplicate key value violates unique constraint' in
            error.exception.message
        )

    @mute_logger('openerp.sql_db')
    def test_raises_on_create_duplicate_nhs_num(self):
        """
        Test that an exception is raised if patient is create with same
        NHS number as another patient
        """
        vals = self.patient_data.copy()
        vals.update(
            {
                'patient_identifier': self.existing_nhs_number,
                'other_identifier': 'test_hospital_number',
                'given_name': 'Test',
                'family_name': 'Patient'
            }
        )
        with self.assertRaises(IntegrityError) as error:
            self.patient_model.create(vals)
        self.assertTrue(
            'duplicate key value violates unique constraint' in
            error.exception.message
        )

    @mute_logger('openerp.sql_db')
    def test_raises_on_write_with_duplicate_hosp_num(self):
        """
        Test that an exception is raise if a patient record is written to but
        the identifiers submitted are already in use by another patient
        """
        second_patient = self.test_utils.create_and_register_patient()
        with self.assertRaises(IntegrityError) as error:
            second_patient.write(
                {
                    'other_identifier': self.existing_hospital_number,
                    'given_name': 'Test',
                    'family_name': 'Patient'
                }
            )
        self.assertTrue(
            'duplicate key value violates unique constraint' in
            error.exception.message
        )

    @mute_logger('openerp.sql_db')
    def test_raises_on_write_with_duplicate_nhs_num(self):
        """
        Test that an exception is raise if a patient record is written to but
        the identifiers submitted are already in use by another patient
        """
        second_patient = self.test_utils.create_and_register_patient()
        with self.assertRaises(IntegrityError) as error:
            second_patient.write(
                {
                    'patient_identifier': self.existing_nhs_number,
                    'given_name': 'Test',
                    'family_name': 'Patient'
                }
            )
        self.assertTrue(
            'duplicate key value violates unique constraint' in
            error.exception.message
        )

    def test_create_new_patient(self):
        """
        Test that we can create a patient
        """
        vals = self.patient_data.copy()
        vals.update(
            {
                'other_identifier': str(uuid4()),
                'given_name': 'Test',
                'family_name': 'Patient'
            }
        )
        patient = self.patient_model.create(vals)
        self.assertTrue(patient, 'Failed to create patient')

    def test_write_patient(self):
        """
        Test that we can write to an existing patient
        """
        self.test_utils.patient.write(
            {
                'given_name': 'Joe Bob',
                'title': 'Mr',
            }
        )
        self.assertEqual(self.test_utils.patient.given_name, 'Joe Bob')
