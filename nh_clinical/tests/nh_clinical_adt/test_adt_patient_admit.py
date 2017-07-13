from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestAdtPatientAdmit(TransactionCase):
    """
    Test the nh.clinical.adt.patient.admit model with is called by the ADT
    """

    def setUp(self):
        super(TestAdtPatientAdmit, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.admit_model = self.env['nh.clinical.adt.patient.admit']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.user_model = self.env['res.users']
        self.category_model = self.env['res.partner.category']
        self.nurse_role = \
            self.category_model.search([('name', '=', 'Nurse')])[0]
        self.test_utils.create_locations()
        self.test_utils.create_patient()
        self.patient = self.test_utils.patient
        self.existing_nhs_number = self.patient.patient_identifier
        self.existing_hospital_number = self.patient.other_identifier
        self.doctors = """[{
                'type': 'c',
                'code': 'CON01',
                'title': 'Dr.',
                'given_name': 'Consulting',
                'family_name': 'Doctor',
                'gender': 'F'
            }, {
                'type': 'r',
                'code': 'REF01',
                'title': 'dr.',
                'given_name': 'Referring',
                'family_name': 'Doctor',
                'gender': 'M'
            }]"""

    def test_admit_patient(self):
        """ Test that can admit a patient """
        admit_data = {
            'other_identifier': self.existing_hospital_number,
            'start_date': '2015-04-30 17:00:00',
            'doctors': self.doctors,
            'code': 'TESTADMISSION01',
            'location': 'U'
        }
        activity_id = self.admit_model.create_activity({}, admit_data)
        activity = self.activity_model.browse(activity_id)
        activity.complete()
        admission = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.patient.admission'],
                ['state', '=', 'completed'],
                ['creator_id', '=', activity_id]
            ]
        )
        self.assertTrue(admission, msg="Admission not found!")
        self.assertEqual(admission.data_ref.con_doctor_ids[0].code, 'CON01',
                         msg="Wrong doctor data")
        self.assertEqual(admission.data_ref.ref_doctor_ids[0].code, 'REF01',
                         msg="Wrong doctor data")
        self.assertEqual(activity.parent_id.data_model, 'nh.clinical.spell')
        self.assertEqual(activity.parent_id.patient_id.id, self.patient.id)

    def test_raises_when_user_no_pos(self):
        """
        Test that raises error when the user used to admit the patient isn't
        related to a Point Of Service
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
        admit_data = {
            'other_identifier': 'TEST002',
            'location': 'U'
        }
        with self.assertRaises(except_orm) as error:
            self.admit_model.sudo(no_pos_user).create_activity(
                {}, admit_data)
        self.assertEqual(
            error.exception.value,
            'POS location is not set for user.login = no_pos!'
        )

    def test_raises_no_location(self):
        """
        Test that it raises an exception when trying to admit a patient
         without
        a location
        """
        admit_data = {
            'other_identifier': 'TEST002'
        }
        with self.assertRaises(except_orm) as error:
            self.admit_model.create_activity({}, admit_data)
        self.assertEqual(
            error.exception.value,
            'Location must be set for admission!'
        )

    def test_raises_no_identifier(self):
        """
        Test that it raises an exception when trying to admit a patient
         without
        any identifiers
        """
        admit_data = {
            'location': 'U'
        }
        with self.assertRaises(except_orm) as error:
            self.admit_model.create_activity({}, admit_data)
        self.assertEqual(
            error.exception.value,
            'Patient\'s NHS or Hospital numbers must be provided'
        )

    def test_admit_with_nhs_number(self):
        """ Test can admit patient with NHS Number """
        admit_data = {
            'patient_identifier': self.existing_nhs_number,
            'start_date': '2015-04-30 17:00:00',
            'doctors': self.doctors,
            'code': 'TESTADMISSION02',
            'location': 'U'
        }
        activity_id = self.admit_model.create_activity({}, admit_data)
        activity = self.activity_model.browse(activity_id)
        activity.complete()
        admission = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.patient.admission'],
                ['state', '=', 'completed'],
                ['creator_id', '=', activity_id]
            ]
        )
        self.assertTrue(admission, msg="Admission not found!")
        self.assertEqual(admission.data_ref.con_doctor_ids[0].code, 'CON01',
                         msg="Wrong doctor data")
        self.assertEqual(admission.data_ref.ref_doctor_ids[0].code, 'REF01',
                         msg="Wrong doctor data")
        self.assertEqual(activity.parent_id.data_model, 'nh.clinical.spell')
        self.assertEqual(activity.parent_id.patient_id.id, self.patient.id)
