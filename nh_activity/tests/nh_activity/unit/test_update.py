from openerp.tests.common import TransactionCase


class TestUpdate(TransactionCase):
    """
    Test the update method on nh_activity. At the nh_activity module level the
    update_activity method only returns True as it's used as a hook later on
    """

    EVENT_TRIGGERED = False
    DATA_MODEL_ACTIVITY_ID = None
    
    def setUp(self):
        """ Set up the tests """
        super(TestUpdate, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.test_activity_data_model = self.env['test.activity.data.model']
        self.EVENT_TRIGGERED = False
        self.DATA_MODEL_ACTIVITY_ID = False

        def patch_data_model_event(*args, **kwargs):
            self.EVENT_TRIGGERED = True
            self.DATA_MODEL_ACTIVITY_ID = args[3]
            return True

        self.test_activity_data_model._patch_method(
            'update_activity',
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
        self.test_activity_data_model._revert_method('update_activity')
        super(TestUpdate, self).tearDown()
        
    def test_update_activity(self):
        """
        Test that the update_activity method returns True when an update
        is successful
        """
        self.assertTrue(self.activity.update_activity())

    def test_calls_data_model_event(self):
        """
        Test that the update_activity method on the model defined in the
        data_model of of the activity is called when calling update_activity
        on the nh.activity model
        """
        self.activity.update_activity()
        self.assertTrue(self.EVENT_TRIGGERED)

    def test_data_model_activity_id(self):
        """
        Test that the update_activity method on the model defined in the
        data_model of the activity is called with the activity id
        """
        self.activity.update_activity()
        self.assertEqual(
            self.activity.id,
            self.DATA_MODEL_ACTIVITY_ID
        )
