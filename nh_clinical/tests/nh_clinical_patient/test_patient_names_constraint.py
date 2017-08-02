from openerp.tests.common import TransactionCase
from uuid import uuid4
from openerp.osv.osv import except_orm


class TestPatientNamesConstraint(TransactionCase):
    """
    Test the constraints on the patient's family and given name
    """

    def setUp(self):
        super(TestPatientNamesConstraint, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.create_locations()
        self.nhs_number = str(uuid4())
        self.hospital_number = str(uuid4())

    def test_raises_no_family_name(self):
        """
        Test that an exception is raised when creating a patient without a
        surname
        """
        with self.assertRaises(except_orm) as error:
            self.patient_model.create({
                'other_identifier': self.hospital_number,
                'patient_identifier': self.nhs_number,
                'given_name': 'Colin'
            })
        self.assertEqual(
            error.exception.value,
            'Patient record must have valid Given and Family Names'
        )

    def test_raises_no_given_name(self):
        """
        Test that an exception is raised when creating a patient without a
        first name
        """
        with self.assertRaises(except_orm) as error:
            self.patient_model.create({
                'other_identifier': self.hospital_number,
                'patient_identifier': self.nhs_number,
                'family_name': 'Wren'
            })
        self.assertEqual(
            error.exception.value,
            'Patient record must have valid Given and Family Names'
        )

    def test_raises_spacey_family_name(self):
        """
        Test that an exception is raised when creating a patient with a
        surname made of spaces
        """
        with self.assertRaises(except_orm) as error:
            self.patient_model.create({
                'other_identifier': self.hospital_number,
                'patient_identifier': self.nhs_number,
                'given_name': 'Colin',
                'family_name': ' '
            })
        self.assertEqual(
            error.exception.value,
            'Patient record must have valid Given and Family Names'
        )

    def test_raises_spacey_given_name(self):
        """
        Test that an exception is raised when creating a patient with a
        first name made of spaces
        """
        with self.assertRaises(except_orm) as error:
            self.patient_model.create({
                'other_identifier': self.hospital_number,
                'patient_identifier': self.nhs_number,
                'given_name': ' ',
                'family_name': 'Wren'
            })
        self.assertEqual(
            error.exception.value,
            'Patient record must have valid Given and Family Names'
        )

    def test_creates_patient(self):
        """ Test that we can create a patient if all good """
        patient = self.patient_model.create({
            'other_identifier': self.hospital_number,
            'patient_identifier': self.nhs_number,
            'given_name': 'Colin',
            'family_name': 'Wren'
        })
        self.assertEqual(patient.given_name, 'Colin')
        self.assertEqual(patient.family_name, 'Wren')
