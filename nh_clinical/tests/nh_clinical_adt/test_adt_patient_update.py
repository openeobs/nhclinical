from openerp.tests.common import TransactionCase
# from openerp.osv.osv import except_osv
from openerp.osv.orm import except_orm
# from psycopg2 import IntegrityError
# from openerp.tools.misc import mute_logger
import uuid


class TestAdtPatientUpdate(TransactionCase):
    """
    Test the nh.clinical.adt.patient.update - Patient Update via ADT model
    """

    def setUp(self):
        super(TestAdtPatientUpdate, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.update_model = self.env['nh.clinical.adt.patient.update']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.create_locations()
        self.test_utils.create_patient()
        self.existing_nhs_number = self.test_utils.patient.patient_identifier
        self.existing_hospital_number = \
            self.test_utils.patient.other_identifier

    def test_update_using_hospital_number(self):
        """
        Test that can update patient record with Hospital number as
        patient identifier
        """
        update_data = {
            'family_name': 'Fupdate',
            'given_name': 'Gupdate',
            'other_identifier': self.existing_hospital_number,
            'middle_names': 'Mupdate',
            'patient_identifier': 'TEST001',
            'dob': '2000-10-01 00:00:00',
            'gender': 'F',
            'sex': 'F',
            'title': 'mr'
        }
        update_activity_id = self.update_model.create_activity({}, {})
        update_activity = self.activity_model.browse(update_activity_id)
        update_activity.submit(update_data)
        self.assertTrue(
            update_activity.complete()
        )
        patient = self.test_utils.patient
        self.assertEqual(
            update_data['family_name'],
            patient.family_name,
            msg="Patient Update: wrong patient data")
        self.assertEqual(
            update_data['given_name'],
            patient.given_name,
            msg="Patient Update: wrong patient data")
        self.assertEqual(
            update_data['other_identifier'],
            patient.other_identifier,
            msg="Patient Update: wrong patient data")
        self.assertEqual(
            update_data['dob'],
            patient.dob,
            msg="Patient Update: wrong patient data")
        self.assertEqual(
            update_data['gender'],
            patient.gender,
            msg="Patient Update: wrong patient data")
        self.assertEqual(
            update_data['sex'],
            patient.sex,
            msg="Patient Update: wrong patient data")

    def test_update_using_nhs_number(self):
        """
        Test can update patient record using NHS Number as patient
        identifier
        """
        update_data = {
            'family_name': 'Fupdate',
            'given_name': 'Gupdate',
            'other_identifier': 'TEST002',
            'patient_identifier': self.existing_nhs_number,
            'dob': '2000-10-01 00:00:00',
            'gender': 'F',
            'sex': 'F'
        }
        update_activity_id = self.update_model.create_activity({}, {})
        update_activity = self.activity_model.browse(update_activity_id)
        update_activity.submit(update_data)
        self.assertTrue(
            update_activity.complete()
        )

    def test_raises_error_when_no_identifiers(self):
        """
        Test raises an error when attempting update with no identifiers given
        """
        update_data = {
            'family_name': 'Fupdate',
            'given_name': 'Gupdate',
            'dob': '2000-10-01 00:00:00',
            'gender': 'F',
            'sex': 'F'
        }

        update_activity_id = self.update_model.create_activity({}, {})
        update_activity = self.activity_model.browse(update_activity_id)
        with self.assertRaises(except_orm) as error:
            update_activity.submit(update_data)
        self.assertEqual(
            error.exception.value,
            'Patient\'s NHS or Hospital numbers must be provided'
        )

    def test_raises_error_when_wrong_hospital_no(self):
        """
        Test raises an error when attempting update with hospital number
        not in system
        """
        update_data = {
            'family_name': 'Fupdate',
            'given_name': 'Gupdate',
            'other_identifier': uuid.uuid4(),
            'dob': '2000-10-01 00:00:00',
            'gender': 'F',
            'sex': 'F'
        }

        update_activity_id = self.update_model.create_activity({}, {})
        update_activity = self.activity_model.browse(update_activity_id)
        with self.assertRaises(except_orm) as error:
            update_activity.submit(update_data)
        self.assertEqual(
            error.exception.value,
            'There is no patient in system with credentials provided'
        )

    def test_raises_error_when_wrong_nhs_no(self):
        """
        Test raises an error when attempting update with NHS number
        not in system
        """
        update_data = {
            'family_name': 'Fupdate',
            'given_name': 'Gupdate',
            'patient_identifier': uuid.uuid4(),
            'dob': '2000-10-01 00:00:00',
            'gender': 'F',
            'sex': 'F'
        }

        update_activity_id = self.update_model.create_activity({}, {})
        update_activity = self.activity_model.browse(update_activity_id)
        with self.assertRaises(except_orm) as error:
            update_activity.submit(update_data)
        self.assertEqual(
            error.exception.value,
            'There is no patient in system with credentials provided'
        )
