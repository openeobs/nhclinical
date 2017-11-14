from openerp.tests.common import TransactionCase


class TestUpdate(TransactionCase):
    """
    Test the update method on nh_activity. At the nh_activity module level the
    update_activity method only returns True as it's used as a hook later on
    """

    EVENT_TRIGGERED = None
    
    def setUp(self):
        """ Set up the tests """
        super(TestUpdate, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.EVENT_TRIGGERED = None

        def patch_data_model_event(*args, **kwargs):
            self.EVENT_TRIGGERED = kwargs.get('callback')
            return True

        self.activity_model._patch_method(
            'data_model_event',
            patch_data_model_event
        )

    def tearDown(self):
        """
        Remove any patches used for the test
        """
        self.activity_model._revert_method('data_model_event')
        super(TestUpdate, self).tearDown()
        
    def test_update_activity(self):
        """
        Test that the update_activity method returns True when an update
        is successful
        """
        activity_id = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )
        self.assertTrue(
            self.activity_model.update_activity(activity_id),
            msg="Event call failed"
        )

    def test_calls_data_model_event(self):
        """
        Test that the data_model_event decorator is called with the
        update_activity event
        """
        activity_id = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )
        self.activity_model.update_activity(activity_id)
        self.assertEqual(
            self.EVENT_TRIGGERED,
            'update_activity',
            msg="Event call failed"
        )
