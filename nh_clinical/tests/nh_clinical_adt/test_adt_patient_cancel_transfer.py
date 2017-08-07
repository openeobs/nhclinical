from uuid import uuid4

from openerp.osv.osv import except_orm
from openerp.tests.common import TransactionCase


class TestAdtPatientCancelTransfer(TransactionCase):
    """
    Test the nh.clinical.adt.patient.cancel_transfer model used in ADT
    messaging to cancel a transfer
    """

    def setUp(self):
        super(TestAdtPatientCancelTransfer, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.cancel_model = self.env['nh.clinical.adt.patient.cancel_transfer']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.admit_and_place_patient()
        self.patient = self.test_utils.patient
        self.existing_nhs_number = self.patient.patient_identifier
        self.existing_hospital_number = self.patient.other_identifier
        self.test_utils.transfer_patient(
            location_code=self.test_utils.other_ward.code)

    def test_raises_cancel_no_patient_info(self):
        """
        Test that an exception is raised when trying to cancel a transfer
        without any patient identifiers
        """
        activity_id = self.cancel_model.create_activity({}, {})
        activity = self.activity_model.browse(activity_id)
        with self.assertRaises(except_orm) as error:
            activity.submit({})
        self.assertEqual(
            error.exception.value,
            'Patient\'s NHS or Hospital numbers must be provided'
        )

    def test_raises_cancel_incorrect_patient_info(self):
        """
        Test that an exception is raised on trying to cancel a transfer for a
        patient that does not exist
        """
        cancel_transfer_data = {
            'other_identifier': uuid4()
        }
        with self.assertRaises(except_orm) as error:
            self.cancel_model.create_activity({}, cancel_transfer_data)
        self.assertEqual(
            error.exception.value,
            'There is no patient in system with credentials provided'
        )

    def test_raises_cancel_no_transfer(self):
        """
        Test that an exception is raised on trying to cancel a transfer for a
        patient that does not have a previous transfer
        :return:
        """
        other_patient = self.test_utils.create_and_register_patient(
            set_instance_variables=False)
        self.test_utils.admit_patient(
            hospital_number=other_patient.other_identifier,
            patient_id=other_patient.id
        )
        cancel_transfer_data = {
            'other_identifier': other_patient.other_identifier
        }
        with self.assertRaises(except_orm) as error:
            self.cancel_model.create_activity({}, cancel_transfer_data)
        self.assertEqual(
            error.exception.value,
            'There is no transfer for patient with id {}'.format(
                other_patient.id)
        )

    def test_cancel_transfer(self):
        """ Test that we can cancel a transfer """
        cancel_transfer_data = {
            'other_identifier': self.existing_hospital_number
        }
        activity_id = self.cancel_model.create_activity(
            {}, cancel_transfer_data)
        activity = self.activity_model.browse(activity_id)
        activity.complete()
        self.assertEqual(activity.data_ref.transfer_id.state, 'cancelled')
