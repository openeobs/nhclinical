import logging

from openerp.tests import common

_logger = logging.getLogger(__name__)


class TestClinicalPatient(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestClinicalPatient, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.patient_pool = cls.registry('nh.clinical.patient')

    def test_family(self):
        # family, given and middle names
        self.assertEquals(
            'Smith, John Clarke',
            self.patient_pool._family('Smith', 'John', 'Clarke')
        )
        # family, given, no middle
        self.assertEquals(
            'Smith, John',
            self.patient_pool._family('Smith', 'John', '')
        )
        # family and middle, no given name
        self.assertEquals(
            'Smith, Clarke',
            self.patient_pool._family('Smith', '', 'Clarke')
        )
        # family name only
        self.assertEquals(
            'Smith',
            self.patient_pool._family('Smith', '', '')
        )
        # no family, given and middle names only
        self.assertEqual(
            'John Clarke',
            self.patient_pool._family('', 'John', 'Clarke')
        )
        # given name only
        self.assertEquals(
            'John',
            self.patient_pool._family('', 'John', '')
        )
        # middle names only
        self.assertEquals(
            'Clarke',
            self.patient_pool._family('', '', 'Clarke')
        )
        # no names
        self.assertEquals('', self.patient_pool._family('', '', ''))

    def test_given(self):
        # family, given and middle names
        self.assertEquals(
            'John Clarke Smith',
            self.patient_pool._given('Smith', 'John', 'Clarke')
        )
        # family, given, no middle
        self.assertEquals(
            'John Smith',
            self.patient_pool._given('Smith', 'John', '')
        )
        # family and middle, no given name
        self.assertEquals(
            'Clarke Smith',
            self.patient_pool._given('Smith', '', 'Clarke')
        )
        # family name only
        self.assertEquals(
            'Smith',
            self.patient_pool._given('Smith', '', '')
        )
        # no family, given and middle names only
        self.assertEqual(
            'John Clarke',
            self.patient_pool._given('', 'John', 'Clarke')
        )
        # given name only
        self.assertEquals(
            'John',
            self.patient_pool._given('', 'John', '')
        )
        # middle names only
        self.assertEquals(
            'Clarke',
            self.patient_pool._given('', '', 'Clarke')
        )
        # no names
        self.assertEquals('', self.patient_pool._given('', '', ''))

    def test_get_fullname(self):
        pass

    def test_get_name(self):
        pass

    def test_check_hospital_number(self):
        pass

    def test_check_nhs_number(self):
        pass



