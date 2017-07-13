from openerp.tests.common import TransactionCase
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from openerp.osv.orm import except_orm
from datetime import datetime


class TestAdtPatientDischarge(TransactionCase):
    """
    Test the nh.clinical.adt.patient.discharge method used in ADT messaging
    """

    def setUp(self):
        super(TestAdtPatientDischarge, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.discharge_model = self.env['nh.clinical.adt.patient.discharge']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.user_model = self.env['res.users']
        self.category_model = self.env['res.partner.category']
        self.nurse_role = \
            self.category_model.search([('name', '=', 'Nurse')])[0]
        self.test_utils.admit_and_place_patient()
        self.patient = self.test_utils.patient
        self.existing_nhs_number = self.patient.patient_identifier
        self.existing_hospital_number = self.patient.other_identifier

    def test_discharge_patient(self):
        """ Test that we can discharge a patient """
        discharge_data = {
            'other_identifier': self.existing_hospital_number,
            'discharge_date': '2015-05-02 18:00:00',
            'location': 'TEST_DISCHARGE'
        }
        activity_id = self.discharge_model.create_activity({}, discharge_data)
        activity = self.activity_model.browse(activity_id)
        self.assertEqual(
            self.patient.id,
            activity.data_ref.patient_id.id,
            msg="Wrong patient id")
        self.assertEqual(activity.parent_id.data_model, 'nh.clinical.spell')
        self.assertEqual(activity.parent_id.patient_id.id, self.patient.id)
        activity.complete()
        discharge_id = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.patient.discharge'],
                ['state', '=', 'completed'],
                ['creator_id', '=', activity_id]
            ]
        )
        self.assertTrue(discharge_id, msg="Discharge not found!")

    def test_raises_no_patient_info(self):
        """ Test raises an exception if no patient identifiers provided """
        discharge_data = {
            'discharge_date': '2015-05-02 18:00:00',
            'location': 'TEST_DISCHARGE'
        }
        with self.assertRaises(except_orm) as error:
            self.discharge_model.create_activity({}, discharge_data)
        self.assertEqual(
            error.exception.value,
            'Patient\'s NHS or Hospital numbers must be provided'
        )

    def test_raises_user_no_pos(self):
        """
        Test raises an exception when carrying out discharge
        as user without a POS
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
        discharge_data = {
            'other_identifier': self.existing_hospital_number,
            'discharge_date': '2015-05-02 18:00:00',
            'location': 'TEST_DISCHARGE'
        }
        with self.assertRaises(except_orm) as error:
            self.discharge_model.sudo(no_pos_user)\
                .create_activity({}, discharge_data)
        self.assertEqual(
            error.exception.value,
            'POS location is not set for user.login = no_pos!'
        )

    def test_discharge_with_nhs_number(self):
        """
        Test that we can discharge a user by providing their NHS number
        """
        discharge_data = {
            'patient_identifier': self.existing_nhs_number,
            'discharge_date': '2015-05-02 18:00:00',
            'location': 'TEST_DISCHARGE'
        }
        activity_id = self.discharge_model.create_activity({}, discharge_data)
        activity = self.activity_model.browse(activity_id)
        self.assertEqual(
            self.patient.id,
            activity.data_ref.patient_id.id,
            msg="Wrong patient id")
        self.assertEqual(activity.parent_id.data_model, 'nh.clinical.spell')
        self.assertEqual(activity.parent_id.patient_id.id, self.patient.id)
        activity.complete()
        discharge_id = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.patient.discharge'],
                ['state', '=', 'completed'],
                ['creator_id', '=', activity_id]
            ]
        )
        self.assertTrue(discharge_id, msg="Discharge not found!")

    def test_raises_no_location(self):
        """
        Test that an exception is raises when trying to discharge a patient
        without a location being provided
        """
        discharge_data = {
            'other_identifier': self.existing_hospital_number,
            'discharge_date': '2015-05-02 18:00:00'
        }
        with self.assertRaises(except_orm) as error:
            self.discharge_model.create_activity({}, discharge_data)
        self.assertEqual(
            error.exception.value,
            'Missing location!'
        )

    def test_discharge_non_admitted_patient(self):
        """ TEst we can discharge a patient who has not been admitted """
        test_patient = self.test_utils.create_and_register_patient()
        discharge_data = {
            'other_identifier': test_patient.other_identifier,
            'discharge_date': '2015-05-02 18:00:00',
            'location': 'U'
        }
        activity_id = self.discharge_model.create_activity({}, discharge_data)
        activity = self.activity_model.browse(activity_id)
        activity.complete()
        discharge_id = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.patient.discharge'],
                ['state', '=', 'completed'],
                ['creator_id', '=', activity_id]
            ]
        )
        self.assertTrue(discharge_id, msg="Discharge not found!")

    def test_raises_already_discharged_patient(self):
        """
        Test an exception is raised if the patient is already discharged
        when we try to discharge them
        """
        discharge_data = {
            'other_identifier': self.existing_hospital_number,
            'discharge_date': '2015-05-02 18:00:00',
            'location': 'U'
        }
        activity_id = self.discharge_model.create_activity({}, discharge_data)
        activity = self.activity_model.browse(activity_id)
        activity.complete()
        with self.assertRaises(except_orm) as error:
            self.discharge_model.create_activity({}, discharge_data)
        self.assertEqual(
            error.exception.value,
            'Patient is already discharged!'
        )

    def test_sets_date_to_now_if_not_sent(self):
        """ Test that datetime.now() is used if no date is provided """
        test_patient = self.test_utils.create_and_register_patient()
        discharge_data = {
            'other_identifier': test_patient.other_identifier,
            'location': 'U'
        }
        activity_id = self.discharge_model.create_activity({}, discharge_data)
        activity = self.activity_model.browse(activity_id)
        activity.complete()
        discharge_id = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.patient.discharge'],
                ['state', '=', 'completed'],
                ['creator_id', '=', activity_id]
            ]
        )
        discharge_date = datetime.strptime(discharge_id.date_terminated, DTF)
        now = datetime.now()
        self.assertEqual(discharge_date.year, now.year)
        self.assertEqual(discharge_date.month, now.month)
        self.assertEqual(discharge_date.day, now.day)
