from openerp.tests.common import TransactionCase
from openerp.osv.osv import except_orm


class TestApiCancelTransfer(TransactionCase):
    """ Test the cancel_transfer method of nh.clinical.api """

    def setUp(self):
        super(TestApiCancelTransfer, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.api_model = self.env['nh.clinical.api']
        self.activity_model = self.env['nh.activity']
        self.patient_model = self.env['nh.clinical.patient']
        self.test_utils.admit_and_place_patient()
        self.hospital_number = self.test_utils.patient.other_identifier
        self.test_utils.transfer_patient(
            location_code=self.test_utils.other_ward.code)

    def test_cancel_transfer(self):
        """ Test we can cancel a transfer """
        self.api_model.cancel_transfer(self.hospital_number)
        activity = self.activity_model.search(
            [
                ['data_model', '=', 'nh.clinical.adt.patient.cancel_transfer'],
                ['patient_id', '=', self.test_utils.patient.id]
            ]
        )
        self.assertTrue(activity,
                        msg="Cancel Transfer Activity not generated")
        self.assertEqual(activity.state, 'completed')

    def test_raises_no_patient_info(self):
        """ Test that an exception is thrown when passing no patient info """
        with self.assertRaises(except_orm) as error:
            self.api_model.cancel_transfer('')
        self.assertEqual(
            error.exception.value,
            'Patient\'s NHS or Hospital numbers must be provided'
        )
