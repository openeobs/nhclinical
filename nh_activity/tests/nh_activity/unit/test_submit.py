from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestSubmit(TransactionCase):
    """
    Test the submit() method of the nh_activity model
    """

    EVENT_TRIGGERED = False
    DATA_MODEL_ACTIVITY_ID = None

    def setUp(self):
        """
        Set up the tests
        """
        super(TestSubmit, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.test_activity_data_model = self.env['test.activity.data.model']
        self.EVENT_TRIGGERED = False
        self.DATA_MODEL_ACTIVITY_ID = None

        def patch_data_model_event(*args, **kwargs):
            self.EVENT_TRIGGERED = True
            self.DATA_MODEL_ACTIVITY_ID = args[3]
            return True

        self.test_activity_data_model._patch_method(
            'submit',
            patch_data_model_event
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
        self.test_activity_data_model._revert_method('submit')
        super(TestSubmit, self).tearDown()

    def test_submit(self):
        """
        Test that submit returns True
        """
        self.assertTrue(self.activity.submit({}))

    def test_no_vals_dict(self):
        """
        Test that raises an exception if no vals dict passed
        """
        with self.assertRaises(TypeError):
            self.activity.submit()

    def test_vals_not_dict(self):
        """
        Test that raises an exception if the vals passed isn't a dictionary
        """
        with self.assertRaises(except_orm):
            self.activity.submit('this aint no dict')

    def test_calls_data_model_event(self):
        """
        Test that the submit method on the model defined in the
        data_model of of the activity is called when calling submit
        on the nh.activity model
        """
        self.activity.submit({})
        self.assertTrue(self.EVENT_TRIGGERED)

    def test_data_model_activity_id(self):
        """
        Test that the submit method on the model defined in the
        data_model of the activity is called with the activity id
        """
        self.activity.submit({})
        self.assertEqual(
            self.activity.id,
            self.DATA_MODEL_ACTIVITY_ID
        )
