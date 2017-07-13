from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestAdtPatientTransfer(TransactionCase):
    """
    Test the nh.clinical.adt.patient.transfer model used in ADT messaging
    to transfer a patient
    """

    def setUp(self):
        super(TestAdtPatientTransfer, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.transfer_model = self.env['nh.clinical.adt.patient.transfer']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.user_model = self.env['res.users']
        self.category_model = self.env['res.partner.category']
        self.nurse_role = \
            self.category_model.search([('name', '=', 'Nurse')])[0]
        self.test_utils.admit_and_place_patient()
        self.patient = self.test_utils.patient
        self.non_admitted_patient = \
            self.test_utils.create_and_register_patient()
        self.existing_nhs_number = self.patient.patient_identifier
        self.existing_hospital_number = self.patient.other_identifier
        self.other_ward = self.test_utils.other_ward

    def test_transfer_patient(self):
        """ Test that we can transfer a patient """
        transfer_data = {
            'other_identifier': self.existing_hospital_number,
            'location': self.other_ward.code
        }
        activity_id = self.transfer_model.create_activity({}, transfer_data)
        activity = self.activity_model.browse(activity_id)
        self.assertEqual(
            self.patient.id,
            activity.data_ref.patient_id.id,
            msg="Wrong patient id")
        self.assertEqual(
            activity.data_ref.location_id.id,
            self.other_ward.id,
            msg="Wrong location id")
        self.assertEqual(activity.parent_id.data_model, 'nh.clinical.spell')
        self.assertEqual(activity.parent_id.patient_id.id, self.patient.id)
        activity.complete()
        transfer_id = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.patient.transfer'],
                ['state', '=', 'completed'],
                ['creator_id', '=', activity_id]
            ]
        )
        self.assertTrue(transfer_id, msg="Transfer not found!")

    def test_transfer_with_nhs_number(self):
        """ Test can transfer patient using NHS Number """
        transfer_data = {
            'patient_identifier': self.existing_nhs_number,
            'location': self.other_ward.code
        }
        activity_id = self.transfer_model.create_activity({}, transfer_data)
        activity = self.activity_model.browse(activity_id)
        self.assertEqual(
            self.patient.id,
            activity.data_ref.patient_id.id,
            msg="Wrong patient id")
        activity.complete()
        transfer_id = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.patient.transfer'],
                ['state', '=', 'completed'],
                ['creator_id', '=', activity_id]
            ]
        )
        self.assertTrue(transfer_id, msg="Transfer not found!")

    def test_raises_non_admitted_transfer_no_origin(self):
        """
        Test raises an exception when trying to transfer a patient
        who hasn't been admitted without an origin location
        """
        transfer_data = {
            'other_identifier': self.non_admitted_patient.other_identifier,
            'location': self.other_ward.code
        }
        with self.assertRaises(except_orm) as error:
            self.transfer_model.create_activity({}, transfer_data)
        self.assertEqual(
            error.exception.value,
            'No origin location provided.'
        )

    def test_transfer_non_admitted_patient_with_origin(self):
        """
        Test we can transfer a non-admitted patient if we provide a
        origin location
        """
        transfer_data = {
            'other_identifier': self.non_admitted_patient.other_identifier,
            'original_location': self.test_utils.ward.code,
            'location': self.other_ward.code
        }
        activity_id = self.transfer_model.create_activity({}, transfer_data)
        activity = self.activity_model.browse(activity_id)
        self.assertEqual(
            self.non_admitted_patient.id,
            activity.data_ref.patient_id.id,
            msg="Wrong patient id")
        self.assertEqual(
            activity.data_ref.location_id.id,
            self.other_ward.id,
            msg="Wrong location id")
        self.assertEqual(activity.parent_id.data_model, 'nh.clinical.spell')
        self.assertEqual(
            activity.parent_id.patient_id.id,
            self.non_admitted_patient.id)
        activity.complete()
        transfer_id = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.patient.transfer'],
                ['state', '=', 'completed'],
                ['creator_id', '=', activity_id]
            ]
        )
        self.assertTrue(transfer_id, msg="Transfer not found!")

    def test_raises_no_patient_info(self):
        """
        Test raises an exception trying to transfer with no patient information
        """
        transfer_data = {
            'location': self.other_ward.code
        }
        with self.assertRaises(except_orm) as error:
            self.transfer_model.create_activity({}, transfer_data)
        self.assertEqual(
            error.exception.value,
            'Patient\'s NHS or Hospital numbers must be provided'
        )

    def test_raises_no_location_provided(self):
        """
        Test that an exception is raises when trying to transfer without
        providing any location information
        """
        transfer_data = {
            'other_identifier': self.existing_hospital_number
        }
        with self.assertRaises(except_orm) as error:
            self.transfer_model.create_activity({}, transfer_data)
        self.assertEqual(
            error.exception.value,
            'Location must be set for transfer!'
        )

    def test_raises_transfer_no_pos_user(self):
        """
        Test that an exception is raised when trying to transfer with a
        user that is not associated with a Point Of Service
        """
        no_pos_user = self.user_model.create(
            {
                'login': 'no_pos',
                'name': 'No Pos User',
                'pos_id': False,
                'pos_ids': [6, 0, 0],
                'category_id': [[4, self.nurse_role.id]]
            }
        )
        transfer_data = {
            'other_identifier': self.existing_hospital_number,
            'location': self.other_ward.code
        }
        with self.assertRaises(except_orm) as error:
            self.transfer_model.sudo(no_pos_user)\
                .create_activity({}, transfer_data)
        self.assertEqual(
            error.exception.value,
            'POS location is not set for user.login = no_pos!'
        )
