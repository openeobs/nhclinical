from openerp.tests.common import TransactionCase


class TestGetFullname(TransactionCase):
    """ Test the get_fullname method of nh.clinical.patient """

    def setUp(self):
        super(TestGetFullname, self).setUp()
        self.patient_model = self.env['nh.clinical.patient']

    def test_family_given_middle(self):
        """ Test get_fullname with Family, Given Middle """
        name = dict(
            family_name='Smith',
            given_name='John',
            middle_names='Clarke'
        )
        self.assertEquals(
            'Smith, John Clarke', self.patient_model._get_fullname(name))

    def test_family_given_no_middle(self):
        """ Test get_fullname with Family, Given """
        name = dict(
            family_name='Smith',
            given_name='John',
            middle_names=''
        )
        self.assertEquals(
            'Smith, John', self.patient_model._get_fullname(name))

    def test_family_middle_no_given(self):
        """ Test get_fullname with Family, Middle """
        name = dict(
            family_name='Smith',
            given_name='',
            middle_names='Clarke'
        )
        self.assertEquals(
            'Smith, Clarke', self.patient_model._get_fullname(name))

    def test_family_no_middle_no_given(self):
        """ Test get_fullname with only Family name"""
        name = dict(
            family_name='Smith',
            given_name='',
            middle_names=''
        )
        self.assertEquals(
            'Smith,', self.patient_model._get_fullname(name))

    def test_no_family_given_middle(self):
        """ Test get_fullname with no family but given and middle names """
        name = dict(
            family_name='',
            given_name='John',
            middle_names='Clarke'
        )
        self.assertEqual(
            ', John Clarke', self.patient_model._get_fullname(name))

    def test_no_family_given_no_middle(self):
        """ Test get_fullname with given name only """
        name = dict(
            family_name='',
            given_name='John',
            middle_names=''
        )
        self.assertEquals(
            ', John', self.patient_model._get_fullname(name))

    def test_no_family_no_given_middle(self):
        """ Test get_fullname with only middle names """
        name = dict(
            family_name='',
            given_name='',
            middle_names='Clarke'
        )
        self.assertEquals(
            ', Clarke', self.patient_model._get_fullname(name))

    def test_no_names_empty_strings(self):
        """ Test get_fullname with '' as names """
        name = dict(
            family_name='',
            given_name='',
            middle_names=''
        )
        self.assertEquals(',', self.patient_model._get_fullname(name))

    def test_none_middle_name_not_none(self):
        """ Test get_fullname with middle name as None """
        name = dict(
            family_name='Smith',
            given_name='John',
            middle_names=None
        )
        self.assertEquals(
            'Smith, John', self.patient_model._get_fullname(name))

    def test_false_middle_name_not_false(self):
        """ Test get_fullname with middle name as False """
        name = dict(
            family_name='Smith',
            given_name='John',
            middle_names=False
        )
        self.assertEquals(
            'Smith, John', self.patient_model._get_fullname(name))
