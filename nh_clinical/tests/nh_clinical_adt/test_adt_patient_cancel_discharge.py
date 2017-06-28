from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm
import uuid


class TestAdtPatientCancelDischarge(TransactionCase):
    """
    Test the nh.clinical.adt.patient.discharge model used by ADT messaging
    """

    def setUp(self):
        super(TestAdtPatientCancelDischarge, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.cancel_model = \
            self.env['nh.clinical.adt.patient.cancel_discharge']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.admit_and_place_patient()
        self.patient = self.test_utils.patient
        self.existing_nhs_number = self.patient.patient_identifier
        self.existing_hospital_number = self.patient.other_identifier

    def test_cancel_discharge(self):
        """ Test that we can cancel a discharge """
        self.test_utils.discharge_patient(
            hospital_number=self.existing_hospital_number)
        cancel_discharge_data = {
            'other_identifier': self.existing_hospital_number
        }
        activity_id = self.cancel_model.create_activity(
            {}, cancel_discharge_data)
        activity = self.activity_model.browse(activity_id)
        activity.complete()
        self.assertEqual(activity.data_ref.discharge_id.state, 'cancelled')

    def test_raises_no_patient_info(self):
        """
        Test that an exception is raise if there was no patient
        identifiers supplied
        """
        self.test_utils.discharge_patient(
            hospital_number=self.existing_hospital_number)
        activity_id = self.cancel_model.create_activity({}, {})
        activity = self.activity_model.browse(activity_id)
        with self.assertRaises(except_orm) as error:
            activity.submit({})
        self.assertEqual(
            error.exception.value,
            'Patient\'s NHS or Hospital numbers must be provided'
        )

    def test_raises_when_incorrect_patient_info(self):
        """
        Test an exception is raised when the patient identifier
        provided is incorrect
        """
        self.test_utils.discharge_patient(
            hospital_number=self.existing_hospital_number)
        cancel_discharge_data = {
            'other_identifier': uuid.uuid4()
        }
        with self.assertRaises(except_orm) as error:
            self.cancel_model.create_activity({}, cancel_discharge_data)
        self.assertEqual(
            error.exception.value,
            'There is no patient in system with credentials provided'
        )

    def test_raises_when_patient_not_discharged(self):
        """
        Test that an exception is raised when try to cancel a discharge for a
        patient that has not been discharged
        """
        cancel_discharge_data = {
            'other_identifier': self.existing_hospital_number
        }
        with self.assertRaises(except_orm) as error:
            self.cancel_model.create_activity({}, cancel_discharge_data)
        self.assertEqual(
            error.exception.value,
            'There is no completed discharge for patient with id {}'.format(
                self.test_utils.patient.id)
        )
