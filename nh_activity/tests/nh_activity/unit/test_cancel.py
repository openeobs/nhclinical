from openerp.tests.common import TransactionCase


class TestCancel(TransactionCase):
    """ Test the cancel() method of the nh.activity model """

    EVENT_TRIGGERED = False
    DATA_MODEL_ACTIVITY_ID = None

    def setUp(self):
        """
        Set up the tests
        """
        super(TestCancel, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.test_activity_data_model = self.env['test.activity.data.model']
        self.EVENT_TRIGGERED = False
        self.DATA_MODEL_ACTIVITY_ID = None

        def patch_data_model_event(*args, **kwargs):
            self.EVENT_TRIGGERED = True
            self.DATA_MODEL_ACTIVITY_ID = args[3]
            return True

        self.test_activity_data_model._patch_method(
            'cancel',
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
        self.test_activity_data_model._revert_method('cancel')
        super(TestCancel, self).tearDown()

    def test_cancel(self):
        """
        Test that cancel returns True
        """
        cancel = self.activity.cancel()
        self.assertTrue(cancel)

    def test_calls_data_model_event(self):
        """
        Test that the cancel method on the model defined in the data_model of
        of the activity is called when calling cancel on the nh.activity model
        """
        self.activity.cancel()
        self.assertTrue(self.EVENT_TRIGGERED)

    def test_calls_data_model_with_id(self):
        """
        Test that the cancel method on the model defined in the data_model of
        the activity is called with the activity id
        """
        self.activity.cancel()
        self.assertEqual(self.DATA_MODEL_ACTIVITY_ID, self.activity.id)
