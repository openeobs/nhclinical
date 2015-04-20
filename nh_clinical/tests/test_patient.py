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
        # family, given and middle names
        name = dict(family_name='Smith', given_name='John',
                    middle_names='Clarke')
        self.assertEquals('Smith, John Clarke',
                          self.patient_pool._get_fullname(name))
        # family, given, no middle
        name = dict(family_name='Smith', given_name='John', middle_names='')
        self.assertEquals(
            'Smith, John', self.patient_pool._get_fullname(name))
        # family and middle, no given name
        name = dict(family_name='Smith', given_name='', middle_names='Clarke')
        self.assertEquals(
            'Smith, Clarke',self.patient_pool._get_fullname(name))
        # family name only
        name = dict(family_name='Smith', given_name='', middle_names='')
        self.assertEquals(
            'Smith,', self.patient_pool._get_fullname(name))
        # no family, given and middle names only
        name = dict(family_name='', given_name='John', middle_names='Clarke')
        self.assertEqual(
            ', John Clarke', self.patient_pool._get_fullname(name))
        # given name only
        name = dict(family_name='', given_name='John', middle_names='')
        self.assertEquals(
            ', John', self.patient_pool._get_fullname(name))
        # middle names only
        name = dict(family_name='', given_name='', middle_names='Clarke')
        self.assertEquals(
            ', Clarke', self.patient_pool._get_fullname(name))
        # no names
        name = dict(family_name='', given_name='', middle_names='')
        self.assertEquals(',', self.patient_pool._get_fullname(name))
        # None
        name = dict(family_name=None, given_name='', middle_names='')
        self.assertEquals(',', self.patient_pool._get_fullname(name))

    def test_get_name(self):
        pass

    def test_check_hospital_number(self):
        pass

    def test_check_nhs_number(self):
        pass



