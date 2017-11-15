from openerp.tests.common import TransactionCase


class TestComplete(TransactionCase):
    """
    Test the complete method of the nh.activity model
    """

    EVENT_TRIGGERED = False
    DATA_MODEL_ACTIVITY_ID = None

    def setUp(self):
        """
        Set up the tests
        """
        super(TestComplete, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.test_activity_data_model = self.env['test.activity.data.model']
        self.EVENT_TRIGGERED = False
        self.DATA_MODEL_ACTIVITY_ID = None

        def patch_data_model_event(*args, **kwargs):
            self.EVENT_TRIGGERED = True
            self.DATA_MODEL_ACTIVITY_ID = args[3]
            return True

        self.test_activity_data_model._patch_method(
            'complete',
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
        self.test_activity_data_model._revert_method('complete')
        super(TestComplete, self).tearDown()

    def test_complete(self):
        """
        Test that the complete() method returns True
        """
        complete = self.activity.complete()
        self.assertTrue(complete)

    def test_calls_data_model_event(self):
        """
        Test that the data_model_event decorator is called with the
        update_activity event
        """
        self.activity.complete()
        self.assertTrue(self.EVENT_TRIGGERED)

    def test_data_model_with_id(self):
        """
        Test that the complete method on the model defined in the data_model of
        the activity is called with the activity id
        """
        self.activity.complete()
        self.assertEqual(
            self.activity.id,
            self.DATA_MODEL_ACTIVITY_ID
        )
