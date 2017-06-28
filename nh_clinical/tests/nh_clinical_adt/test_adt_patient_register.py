from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm
from openerp.osv.osv import except_osv
from psycopg2 import IntegrityError
from openerp.tools.misc import mute_logger


class TestAdtPatientRegister(TransactionCase):
    """
    Test the nh.clinical.adt.patient.register - Patient Registration via
     ADT model
    """

    def setUp(self):
        super(TestAdtPatientRegister, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.register_model = self.env['nh.clinical.adt.patient.register']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.create_locations()

    def test_register_new_hospital_number(self):
        """ Test registering a new patient with hospital number """
        register_data = {
            'family_name': 'Family',
            'middle_names': 'Middle',
            'given_name': 'Given',
            'other_identifier': 'TEST001',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }
        register_activity_id = self.register_model.create_activity({}, {})
        register_activity = self.activity_model.browse(register_activity_id)
        register_activity.submit(register_data)
        patient_id = register_activity.complete()
        patient = self.patient_model.browse(patient_id)
        self.assertTrue(
            patient,
            msg="Patient Register: patient id not returned")
        self.assertEqual(
            register_data['family_name'],
            patient.family_name,
            msg="Patient Register: wrong patient data registered")
        self.assertEqual(
            register_data['given_name'],
            patient.given_name,
            msg="Patient Register: wrong patient data registered")
        self.assertEqual(
            register_data['other_identifier'],
            patient.other_identifier,
            msg="Patient Register: wrong patient data registered")
        self.assertEqual(
            register_data['dob'],
            patient.dob,
            msg="Patient Register: wrong patient data registered")
        self.assertEqual(
            register_data['gender'],
            patient.gender,
            msg="Patient Register: wrong patient data registered")
        self.assertEqual(
            register_data['sex'],
            patient.sex,
            msg="Patient Register: wrong patient data registered")

    def test_register_new_patient_with_nhs_number(self):
        """ Register a new patient with NHS Number """
        register_data = {
            'family_name': 'Family',
            'given_name': 'Given',
            'patient_identifier': 'TEST001',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }
        register_activity_id = self.register_model.create_activity({}, {})
        register_activity = self.activity_model.browse(register_activity_id)
        register_activity.submit(register_data)
        patient_id = register_activity.complete()
        self.assertTrue(patient_id,
                        msg="Patient Register: patient id not returned")

    def test_register_no_identifiers(self):
        """
        Test raises an error when submitting data for incorrect activity
        """
        register_data = {
            'family_name': 'Family',
            'given_name': 'Given',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }
        register_activity_id = self.register_model.create_activity({}, {})
        register_activity = self.activity_model.browse(register_activity_id)
        register_activity.submit(register_data)
        with self.assertRaises(except_orm) as error:
            register_activity.complete()
        self.assertEqual(
            error.exception.value,
            'Patient record must have NHS and/or Hospital number'
        )

    def test_register_no_names(self):
        """
        Test raises an error when submitting data for incorrect activity
        """
        register_data = {
            'dob': '1984-10-01 00:00:00',
            'patient_identifier': 'TEST001',
            'gender': 'M',
            'sex': 'M'
        }
        register_activity_id = self.register_model.create_activity({}, {})
        register_activity = self.activity_model.browse(register_activity_id)
        register_activity.submit(register_data)
        with self.assertRaises(except_osv) as error:
            register_activity.complete()
        self.assertEqual(
            error.exception.value,
            'Patient must have a full name!'
        )

    @mute_logger('openerp.sql_db')
    def test_register_duplicate_nhs_number(self):
        """
        Test raises an error when submitting duplicate NHS Number
        """
        register_data = {
            'family_name': 'Family',
            'given_name': 'Given',
            'patient_identifier': 'TEST001',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }
        register_activity_id = self.register_model.create_activity({}, {})
        register_activity = self.activity_model.browse(register_activity_id)
        register_activity.submit(register_data)
        register_activity.complete()

        new_register_activity_id = self.register_model.create_activity({}, {})
        new_register_activity = \
            self.activity_model.browse(new_register_activity_id)
        new_register_activity.submit(register_data)
        with self.assertRaises(IntegrityError) as error:
            new_register_activity.complete()
        self.assertTrue(
            'duplicate key value violates unique constraint' in
            error.exception.message
        )

    @mute_logger('openerp.sql_db')
    def test_register_duplicate_hospital_number(self):
        """
        Test raises an error when submitting duplicate NHS Number
        """
        register_data = {
            'family_name': 'Family',
            'given_name': 'Given',
            'other_identifier': 'TEST001',
            'dob': '1984-10-01 00:00:00',
            'gender': 'M',
            'sex': 'M'
        }
        register_activity_id = self.register_model.create_activity({}, {})
        register_activity = self.activity_model.browse(register_activity_id)
        register_activity.submit(register_data)
        register_activity.complete()

        new_register_activity_id = self.register_model.create_activity({}, {})
        new_register_activity = \
            self.activity_model.browse(new_register_activity_id)
        new_register_activity.submit(register_data)
        with self.assertRaises(IntegrityError) as error:
            new_register_activity.complete()
        self.assertTrue(
            'duplicate key value violates unique constraint' in
            error.exception.message
        )
