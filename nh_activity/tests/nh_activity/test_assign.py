from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestAssign(TransactionCase):
    """
    Test the assign() method of the nh.activity model. This method checks that
    the supplied user_id is valid but the bulk of the implementation is in
    the assign() method of nh.activity.data.
    """

    def setUp(self):
        """
        Set up the tests
        """
        super(TestAssign, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.activity_data_model = self.env['nh.activity.data']
        self.user_model = self.env['res.users']
        self.EVENT_TRIGGERED = False

        def mock_assign(*args, **kwargs):
            return True

        self.activity_data_model._patch_method(
            'assign',
            mock_assign
        )

        self.activity = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )

    def tearDown(self):
        """
        Remove any patches set up as part of the tests
        """
        self.activity_data_model._revert_method('assign')
        super(TestAssign, self).tearDown()

    def test_bad_user_id(self):
        """
        Test that assign raises an exception when trying to assign an activity
        with a dodgy user_id
        """
        with self.assertRaises(except_orm):
            self.activity.assign('User ID')
