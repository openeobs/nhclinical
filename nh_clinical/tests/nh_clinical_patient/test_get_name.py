from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestGetName(TransactionCase):
    """ Test the get_name method """

    def setUp(self):
        super(TestGetName, self).setUp()
        self.patient_model = self.env['nh.clinical.patient']

    def test_get_name(self):
        """ Test Family, middle and given names are present in record """
        patient = self.patient_model.create(
            {
                'other_identifier': 'TESTHN001',
                'given_name': 'John',
                'family_name': 'Smith',
                'middle_names': 'Clarke'
            }
        )
        result = patient._get_name(fn=None, args=None)
        self.assertEquals('Smith, John Clarke', result.get(patient.id))

    def test_get_name_with_firstname(self):
        """ Test raises an exception when no first name """
        with self.assertRaises(except_orm):
            patient = self.patient_model.create(
                {
                    'other_identifier': 'TESTHN002',
                    'given_name': 'John'
                }
            )
            patient._get_name(fn=None, args=None)

    def test_get_name_with_no_name(self):
        """ Test raises an exception when no names """
        with self.assertRaises(except_orm):
            patient = self.patient_model.create(
                {
                    'other_identifier': 'TESTHN003'
                }
            )
            patient._get_name(fn=None, args=None)
