import logging

from openerp.tests import common

_logger = logging.getLogger(__name__)


class TestClinicalPatient(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestClinicalPatient, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.patient_pool = cls.registry('nh.clinical.patient')

    def test_get_fullname(self):
        family_name = 'Smith'
        given_name = 'John'
        middle_names = 'Andrew Clarke'

        # no names
        patient_name = dict(family_name='', given_name='', middle_names='')
        self.assertEquals('',
                          self.patient_pool._get_fullname(patient_name))

        # family, given and middle names
        patient_name = {
            'family_name': family_name, 'given_name': given_name,
            'middle_names': middle_names,
        }
        self.assertEquals('Smith, John Andrew Clarke',
                          self.patient_pool._get_fullname(patient_name))

        # family and given name, but no middle names
        patient_name['middle_names'] = ''
        self.assertEquals('Smith, John',
                          self.patient_pool._get_fullname(patient_name))

        # family name, no given name, but middle names
        patient_name['given_name'] = ''
        patient_name['middle_names'] = middle_names
        self.assertEquals('Smith, Andrew Clarke',
                          self.patient_pool._get_fullname(patient_name))

        # family name, no given name, no middle names
        patient_name['middle_names'] = ''
        self.assertEquals('Smith',
                          self.patient_pool._get_fullname(patient_name))

        # No family name, but given and middle names
        patient_name['family_name'] = ''
        patient_name['given_name'] = given_name
        patient_name['middle_names'] = middle_names
        self.assertEquals('John Andrew Clarke',
                          self.patient_pool._get_fullname(patient_name))

        # no family name and no middle names, just given name
        patient_name['middle_names'] = ''
        self.assertEquals('John',
                          self.patient_pool._get_fullname(patient_name))

        # no family name, but middle names and no given name
        patient_name['middle_names'] = middle_names
        patient_name['given_name'] = ''
        self.assertEquals('Andrew Clarke',
                          self.patient_pool._get_fullname(patient_name))

    def test_full_name(self):
        pass

    def test_check_hospital_number(self):
        pass

    def test_check_nhs_number(self):
        pass



