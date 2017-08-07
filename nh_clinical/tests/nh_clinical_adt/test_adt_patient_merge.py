from uuid import uuid4

from openerp.osv.osv import except_orm
from openerp.tests.common import TransactionCase


class TestAdtPatientMerge(TransactionCase):
    """
    Test the nh.clinical.adt.patient.merge method used via ADT Messaging
    to merge patients
    """

    def setUp(self):
        super(TestAdtPatientMerge, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.merge_model = self.env['nh.clinical.adt.patient.merge']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.user_model = self.env['res.users']
        self.category_model = self.env['res.partner.category']
        self.nurse_role = \
            self.category_model.search([('name', '=', 'Nurse')])[0]
        self.test_utils.admit_and_place_patient()
        self.patient = self.test_utils.patient
        self.other_patient = self.test_utils.create_and_register_patient(
            set_instance_variables=False)
        self.other_ward = self.test_utils.other_ward
        self.existing_nhs_number = self.patient.patient_identifier
        self.existing_hospital_number = self.patient.other_identifier

    def test_raises_on_incorrect_from_patient_info(self):
        """
        Test that an exception is raised on being passed incorrect patient
        identifiers
        """
        with self.assertRaises(except_orm) as from_error:
            self.merge_model.create_activity(
                {},
                {
                    'from_identifier': uuid4()
                }
            )
        self.assertEqual(
            from_error.exception.value,
            'There is no patient in system with credentials provided'
        )

    def test_raises_on_incorrect_to_patient_info(self):
        """
        Test that an exception is raised on being passed incorrect patient
        identifiers
        """
        with self.assertRaises(except_orm) as to_error:
            self.merge_model.create_activity(
                {},
                {
                    'into_identifier': uuid4()
                }
            )
        self.assertEqual(
            to_error.exception.value,
            'There is no patient in system with credentials provided'
        )

    def test_raise_missing_source_patient(self):
        """
        Test that en exception is raised when trying to merge two patients and
        the source patient is not in the system
        """
        activity_id = self.merge_model.create_activity(
            {},
            {
                'into_identifier': self.existing_hospital_number
            }
        )
        activity = self.activity_model.browse(activity_id)
        with self.assertRaises(except_orm) as error:
            activity.complete()
        self.assertEqual(
            error.exception.value,
            'Source patient not found in submitted data!'
        )

    def test_raise_missing_destination_patient(self):
        """
        Test that an exception is raised when trying to merge two patients and
        the destination patient is not in the system
        """
        activity_id = self.merge_model.create_activity(
            {},
            {
                'from_identifier': self.existing_hospital_number
            }
        )
        activity = self.activity_model.browse(activity_id)
        with self.assertRaises(except_orm) as error:
            activity.complete()
        self.assertEqual(
            error.exception.value,
            'Destination patient not found in submitted data!'
        )

    def test_merge_two_patients(self):
        """ Test that we can merge two patients """
        merge_data = {
            'from_identifier': self.existing_hospital_number,
            'into_identifier': self.other_patient.other_identifier,
        }
        activity_id = self.merge_model.create_activity({}, merge_data)
        activity = self.activity_model.browse(activity_id)
        from_patient_activities = self.activity_model.search(
            [
                (
                    'patient_id.other_identifier',
                    '=',
                    self.existing_hospital_number
                )
            ]
        )
        self.assertTrue(
            len(from_patient_activities),
            msg="There are no activities to be given to destination patient")
        activity.complete()
        self.assertFalse(
            activity.data_ref.source_patient_id.active,
            msg="Source patient was not deactivated")
        for a in from_patient_activities:
            self.assertEqual(
                a.patient_id.other_identifier,
                self.other_patient.other_identifier
            )
        self.assertEqual(
            activity.data_ref.dest_patient_id.given_name,
            self.other_patient.given_name,
            msg="Destination patient data wrong update")
