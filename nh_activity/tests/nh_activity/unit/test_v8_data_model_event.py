from openerp.tests.common import TransactionCase


class TestV8DataModelEvent(TransactionCase):
    """
    Test the data_model_event decorator for Odoo v8 API
    """

    DECORATED_METHOD_CALLED = False
    DATA_MODEL_METHOD_CALLED = False

    def setUp(self):
        """
        Set up the tests
        """
        super(TestV8DataModelEvent, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.test_activity_data_model = self.env['test.activity.data.model']
        self.DECORATED_METHOD_CALLED = False
        self.DATA_MODEL_METHOD_CALLED = False

        def patch_decorated_method(*args, **kwargs):
            self.DECORATED_METHOD_CALLED = True
            return patch_decorated_method.origin(*args, **kwargs)

        def patch_data_model_method(*args, **kwargs):
            self.DATA_MODEL_METHOD_CALLED = True
            return True

        self.activity_model._patch_method(
            'update_activity',
            patch_decorated_method
        )

        self.test_activity_data_model._patch_method(
            'update_activity',
            patch_data_model_method
        )
        self.activity = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )

    def tearDown(self):
        """
        Clean up after test
        """
        self.activity_model._revert_method('update_activity')
        self.test_activity_data_model._revert_method('update_activity')
        super(TestV8DataModelEvent, self).tearDown()

    def test_decorated_method_called(self):
        """
        Test that the method that has the data_model_event decorator on it
        is called
        """
        self.activity.update_activity()
        self.assertTrue(self.DECORATED_METHOD_CALLED)

    def test_data_model_method_called(self):
        """
        Test that the defined method on the data_model is called when the
        decorator is called
        """
        self.activity.update_activity()
        self.assertTrue(self.DATA_MODEL_METHOD_CALLED)
