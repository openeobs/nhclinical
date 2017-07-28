from openerp.tests.common import TransactionCase


class TestRemoveWhiteSpace(TransactionCase):
    """ Test the _remove_whitespace function on nh.clinical.patient """

    def setUp(self):
        super(TestRemoveWhiteSpace, self).setUp()
        self.patient_model = self.env['nh.clinical.patient']

    def test_removes_whitespace(self):
        """
        Test that white space is removed from string
        """
        string = '      test     String     '
        self.assertEqual(
            'testString',
            self.patient_model._remove_whitespace(string)
        )

    def test_returns_string_no_space(self):
        """
        Test that if string has no white space it just returns that string
        """
        string = 'testString'
        self.assertEqual(
            'testString',
            self.patient_model._remove_whitespace(string)
        )

    def test_returns_none_no_chars_in_string(self):
        """
        TEst that if string is just spaces it returns None instead of ''
        """
        self.assertIsNone(self.patient_model._remove_whitespace('           '))
