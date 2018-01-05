from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestAssign(TransactionCase):
    """
    Test the assign() method of the nh.activity model. This method checks that
    the supplied user_id is valid but the bulk of the implementation is in
    the assign() method of nh.activity.data.
    """

    EVENT_TRIGGERED = False
    DATA_MODEL_ACTIVITY_ID = None

    def setUp(self):
        """
        Set up the tests
        """
        super(TestAssign, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.test_activity_data_model = self.env['test.activity.data.model']
        self.user_model = self.env['res.users']
        self.EVENT_TRIGGERED = False
        self.DATA_MODEL_ACTIVITY_ID = None

        def mock_assign(*args, **kwargs):
            self.EVENT_TRIGGERED = True
            self.DATA_MODEL_ACTIVITY_ID = args[3]
            return True

        self.test_activity_data_model._patch_method(
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
        self.test_activity_data_model._revert_method('assign')
        super(TestAssign, self).tearDown()

    def test_bad_user_id(self):
        """
        Test that assign raises an exception when trying to assign an activity
        with a dodgy user_id
        """
        with self.assertRaises(except_orm):
            self.activity.assign('User ID')

    def test_calls_data_method(self):
        """
        Test that the assign method on the model defined in the data_model of
        of the activity is called when calling assign on the nh.activity model
        """
        self.activity.assign(self.uid)
        self.assertTrue(self.EVENT_TRIGGERED)

    def test_calls_data_method_with_id(self):
        """
        Test that the assign method on the model defined in the data_model of
        the activity is called with the activity id
        """
        self.activity.assign(self.uid)
        self.assertEqual(self.activity.id, self.DATA_MODEL_ACTIVITY_ID)
