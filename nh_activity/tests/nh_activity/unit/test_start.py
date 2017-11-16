from openerp.tests.common import TransactionCase


class TestStart(TransactionCase):
    """
    Test the start method on nh_activity. At the nh_activity module level the
    start method only returns True as it's used as a hook later on
    """

    EVENT_TRIGGERED = False
    DATA_MODEL_ACTIVITY_ID = None

    def setUp(self):
        """ Set up the tests """
        super(TestStart, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.test_activity_data_model = self.env['test.activity.data.model']
        self.EVENT_TRIGGERED = False
        self.DATA_MODEL_ACTIVITY_ID = False

        def patch_data_model_event(*args, **kwargs):
            self.EVENT_TRIGGERED = True
            self.DATA_MODEL_ACTIVITY_ID = args[3]
            return True

        self.test_activity_data_model._patch_method(
            'start',
            patch_data_model_event
        )

        self.activity = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )

    def tearDown(self):
        """
        Remove any patches used for the test
        """
        self.test_activity_data_model._revert_method('start')
        super(TestStart, self).tearDown()

    def test_start(self):
        """
        Test that the start method returns True
        """
        self.assertTrue(self.activity.start())

    def test_calls_data_model_event(self):
        """
        Test that the start method on the model defined in the
        data_model of of the activity is called when calling start
        on the nh.activity model
        """
        self.activity.start()
        self.assertTrue(self.EVENT_TRIGGERED)

    def test_data_model_activity_id(self):
        """
        Test that the start method on the model defined in the
        data_model of the activity is called with the activity id
        """
        self.activity.start()
        self.assertEqual(
            self.activity.id,
            self.DATA_MODEL_ACTIVITY_ID
        )
