from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm
import uuid


class TestAdtPatientCancelAdmit(TransactionCase):
    """ Test the nh.clinical.adt.patient.cancel_admit model used via ADT """

    def setUp(self):
        super(TestAdtPatientCancelAdmit, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.cancel_model = self.env['nh.clinical.adt.patient.cancel_admit']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.create_locations()
        self.test_utils.create_users()
        self.test_utils.create_patient()
        self.spell = self.test_utils.admit_patient()
        self.patient = self.test_utils.patient
        self.existing_nhs_number = self.patient.patient_identifier
        self.existing_hospital_number = self.patient.other_identifier

    def test_raises_on_no_patient_info(self):
        """
        Test that raises an exception when trying to cancel admit with no
        patient information
        """
        activity_id = self.cancel_model.create_activity({}, {})
        activity = self.activity_model.browse(activity_id)
        with self.assertRaises(except_orm) as error:
            activity.submit({})
        self.assertEqual(
            error.exception.value,
            "Patient's Hospital Number must be supplied!"
        )

    def test_raises_error_on_unadmitted_patient(self):
        """
        Test that raises an exception when trying to cancel admit with
        unadmitted patient
        """
        second_patient = self.test_utils.create_and_register_patient()
        cancel_admit_data = {
            'other_identifier': second_patient.other_identifier
        }
        with self.assertRaises(except_orm) as error:
            self.cancel_model.create_activity({}, cancel_admit_data)
        self.assertEqual(
            error.exception.value,
            'There is no started spell for patient with id {}'.format(
                second_patient.id)
        )

    def test_raises_error_on_unregistered_patient(self):
        """
        Test that raises an exception when trying to cancel admit with
        unregistered patient
        """
        cancel_admit_data = {'other_identifier': uuid.uuid4()}
        with self.assertRaises(except_orm) as error:
            self.cancel_model.create_activity({}, cancel_admit_data)
        self.assertEqual(
            error.exception.value,
            'There is no patient in system with credentials provided'
        )

    def test_cancel_admission_with_hospital_no(self):
        """ Test cancels an admission using hospital number """
        cancel_admit_data = {'other_identifier': self.existing_hospital_number}
        activity_id = self.cancel_model.create_activity({}, cancel_admit_data)
        activity = self.activity_model.browse(activity_id)
        activity.complete()
        self.assertEqual(activity.data_ref.admission_id.state, 'cancelled')

    def test_raises_with_nhs_no(self):
        """
        Test raises exception when using NHS Number / patient_identifier
        as this is not supported currently
        """
        cancel_admit_data = {'patient_identifier': self.existing_nhs_number}
        with self.assertRaises(except_orm) as error:
            self.cancel_model.create_activity({}, cancel_admit_data)
        self.assertEqual(
            error.exception.value,
            "Patient's Hospital Number must be supplied!"
        )
