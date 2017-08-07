from uuid import uuid4

from openerp.osv.osv import except_orm
from openerp.tests.common import TransactionCase


class TestApiMerge(TransactionCase):
    """ Test the merge method of nh.clinical.api """

    def setUp(self):
        super(TestApiMerge, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.api_model = self.env['nh.clinical.api']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.admit_and_place_patient()
        self.hospital_number = self.test_utils.patient.other_identifier
        self.nhs_number = self.test_utils.patient.patient_identifier
        self.other_patient = self.test_utils.create_and_register_patient(
            set_instance_variables=False)

    def test_merge_two_patients(self):
        """ Test that we can merge 2 patients """
        merge_data = {
            'from_identifier': self.test_utils.patient.other_identifier
        }

        self.api_model.merge(self.other_patient.other_identifier, merge_data)
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.patient.merge'],
                ['patient_id', '=', self.other_patient.id]
            ]
        )
        self.assertTrue(activity, msg="Merge Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_raises_on_no_source_id(self):
        """ Test that an exception is raised when there's no source id """
        with self.assertRaises(except_orm) as error:
            self.api_model.merge(uuid4(), {})
        self.assertEqual(
            error.exception.value,
            'There is no patient in system with credentials provided'
        )

    def test_raises_on_no_destination_id(self):
        """ Test that an exception is raise when there's no destination id """
        merge_data = {
            'from_identifier': str(uuid4())
        }
        with self.assertRaises(except_orm) as error:
            self.api_model.merge('', merge_data)
        self.assertEqual(
            error.exception.value,
            'Patient\'s NHS or Hospital numbers must be provided'
        )
