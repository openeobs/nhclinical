from uuid import uuid4

from openerp.osv.osv import except_orm
from openerp.tests.common import TransactionCase


class TestAdtSpellUpdate(TransactionCase):
    """
    Test the nh.clinical.adt.spell.update model used via ADT messaging to
    update a patient's spell
    """

    def setUp(self):
        super(TestAdtSpellUpdate, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.update_model = self.env['nh.clinical.adt.spell.update']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.user_model = self.env['res.users']
        self.category_model = self.env['res.partner.category']
        self.nurse_role = \
            self.category_model.search([('name', '=', 'Nurse')])[0]
        self.test_utils.admit_and_place_patient()
        self.patient = self.test_utils.patient
        self.non_admitted_patient = \
            self.test_utils.create_and_register_patient(
                set_instance_variables=False)
        self.existing_nhs_number = self.patient.patient_identifier
        self.existing_hospital_number = self.patient.other_identifier
        self.other_ward = self.test_utils.other_ward
        self.doctors = """[{
            'type': 'c',
            'code': 'CON02',
            'title': 'Dr.',
            'given_name': 'Consulting',
            'family_name': 'Doctor',
            'gender': 'F'
        }, {
            'type': 'r',
            'code': 'REF02',
            'title': 'dr.',
            'given_name': 'Referring',
            'family_name': 'Doctor',
            'gender': 'M'
        }]"""

    def test_update_spell(self):
        """ Test that we can update a patient's spell """
        new_spell_code = str(uuid4())
        update_data = {
            'other_identifier': self.existing_hospital_number,
            'start_date': '2015-05-05 17:00:00',
            'doctors': self.doctors,
            'code': new_spell_code,
            'location': self.test_utils.other_ward.code
        }
        activity_id = self.update_model.create_activity({}, update_data)
        activity = self.activity_model.browse(activity_id)
        self.assertEqual(
            self.patient.id,
            activity.data_ref.patient_id.id,
            msg="Wrong patient id")
        self.assertEqual(
            self.test_utils.other_ward.id,
            activity.data_ref.location_id.id,
            msg="Wrong location id")
        activity.complete()
        spell_activity = self.activity_model.browse(activity.parent_id.id)
        self.assertEqual(
            spell_activity.data_ref.con_doctor_ids[0].code,
            'CON02',
            msg="Wrong doctor data")
        self.assertEqual(
            spell_activity.data_ref.ref_doctor_ids[0].code,
            'REF02',
            msg="Wrong doctor data")
        self.assertEqual(
            spell_activity.data_ref.start_date,
            '2015-05-05 17:00:00')
        self.assertEqual(
            spell_activity.data_ref.code,
            new_spell_code
        )
        self.assertEqual(
            spell_activity.data_ref.location_id.id,
            self.other_ward.id,
            msg="Patient was not moved")

    def test_raises_no_pos_user(self):
        """
        Test an exception is raised when trying to update a spell with a user
        not associated with a Point of Service
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
        update_data = {
            'other_identifier': self.existing_hospital_number,
            'location': self.other_ward.code
        }
        with self.assertRaises(except_orm) as error:
            self.update_model.sudo(no_pos_user)\
                .create_activity({}, update_data)
        self.assertEqual(
            error.exception.value,
            'POS location is not set for user.login = no_pos!'
        )

    def test_raises_no_location(self):
        """
        Test an exception is raised on trying to update spell without supplying
        a location
        """
        update_data = {
            'other_identifier': self.existing_hospital_number
        }
        with self.assertRaises(except_orm) as error:
            self.update_model.create_activity({}, update_data)
        self.assertEqual(
            error.exception.value,
            'Location must be set for spell update!'
        )

    def test_raises_no_patient_info(self):
        """
        Test an exception is raised when trying to update a spell without
        supplying the patient identifiers
        """
        update_data = {
            'location': self.other_ward.code
        }
        with self.assertRaises(except_orm) as error:
            self.update_model.create_activity({}, update_data)
        self.assertEqual(
            error.exception.value,
            'Patient\'s NHS or Hospital numbers must be provided'
        )

    def test_update_without_doctors(self):
        """ Test we can update the spell without supplying doctor data """
        update_data = {
            'other_identifier': self.existing_hospital_number,
            'start_date': '2015-05-05 17:00:00',
            'code': 'TESTADMISSION03',
            'location': self.other_ward.code
        }
        activity_id = self.update_model.create_activity({}, update_data)
        activity = self.activity_model.browse(activity_id)
        activity.complete()
        spell_activity = activity.parent_id
        self.assertFalse(
            spell_activity.data_ref.con_doctor_ids,
            msg="Wrong referring doctor data")
        self.assertFalse(
            spell_activity.data_ref.ref_doctor_ids,
            msg="Wrong consulting doctor data")

    def test_can_update_with_nhs_number(self):
        """ TEst we can update spell using NHS Number """
        new_spell_code = str(uuid4())
        update_data = {
            'patient_identifier': self.existing_nhs_number,
            'start_date': '2015-04-30 17:00:00',
            'doctors': self.doctors,
            'code': new_spell_code,
            'location': self.other_ward.code
        }

        activity_id = self.update_model.create_activity({}, update_data)
        activity = self.activity_model.browse(activity_id)
        self.assertEqual(
            self.patient.id,
            activity.data_ref.patient_id.id,
            msg="Wrong patient id")
        activity.complete()
        spell_activity = self.activity_model.browse(activity.parent_id.id)
        self.assertEqual(
            spell_activity.data_ref.con_doctor_ids[0].code,
            'CON02',
            msg="Wrong doctor data")
        self.assertEqual(
            spell_activity.data_ref.ref_doctor_ids[0].code,
            'REF02',
            msg="Wrong doctor data")
        self.assertEqual(
            spell_activity.data_ref.start_date,
            '2015-04-30 17:00:00')
        self.assertEqual(
            spell_activity.data_ref.code,
            new_spell_code
        )
        self.assertEqual(
            spell_activity.data_ref.location_id.id,
            self.other_ward.id,
            msg="Patient was not moved")

    def test_raises_patient_not_admitted(self):
        """
        TEst an exception is raised when trying to update a spell for a patient
        who is not admitted
        """
        update_data = {
            'other_identifier': self.non_admitted_patient.other_identifier,
            'start_date': '2015-04-30 17:00:00',
            'doctors': self.doctors,
            'code': 'TESTADMISSION0Z',
            'location': self.other_ward.code
        }
        with self.assertRaises(except_orm) as error:
            self.update_model.create_activity({}, update_data)
        self.assertEqual(
            error.exception.value,
            'The patient does not have an open spell!'
        )
