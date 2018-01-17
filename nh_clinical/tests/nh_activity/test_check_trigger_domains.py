from openerp.tests.common import TransactionCase


class TestCheckTriggerDomains(TransactionCase):
    """
    Test that the check_trigger_domains method is returning the correct
    value
    """

    def setUp(self):
        """ Setup the tests """
        super(TestCheckTriggerDomains, self).setUp()

    def test_no_domains(self):
        """
        Test that if no domains are passed that it returns False
        """
        self.assertTrue(False)

    def test_records_found(self):
        """
        Test that if the domain returns records then it returns True
        """
        self.assertTrue(False)

    def test_no_records_found(self):
        """
        Test that if the domains returns no records then it returns False
        """
        self.assertTrue(False)
