from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestV7DataModelEvent(TransactionCase):
    """
    Test the data_model_event decorator for Odoo v7 API
    """

    DECORATED_METHOD_CALLED = False
    DATA_MODEL_METHOD_CALLED = False

    def setUp(self):
        """
        Set up the tests
        """
        super(TestV7DataModelEvent, self).setUp()
        self.activity_model = self.registry('nh.activity')
        self.test_activity_data_model = \
            self.registry('test.activity.data.model')
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
        self.activity_id = self.activity_model.create(
            self.cr,
            self.uid,
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
        super(TestV7DataModelEvent, self).tearDown()

    def test_decorated_method_called(self):
        """
        Test that the method that has the data_model_event decorator on it
        is called
        """
        self.activity_model.update_activity(
            self.cr,
            self.uid,
            self.activity_id
        )
        self.assertTrue(self.DECORATED_METHOD_CALLED)

    def test_id_in_list(self):
        """
        Test that when the decorator receives a list of ids that it uses
        the first one
        """
        self.activity_model.update_activity(
            self.cr,
            self.uid,
            [self.activity_id]
        )
        self.assertTrue(self.DECORATED_METHOD_CALLED)

    def test_id_in_tuple(self):
        """
        Test that when the decorator receives a tuple of ids that it uses
        the first one
        """
        self.activity_model.update_activity(
            self.cr,
            self.uid,
            (self.activity_id)
        )
        self.assertTrue(self.DECORATED_METHOD_CALLED)

    def test_id_bad_type(self):
        """
        Test that an exception is raised if ID isn't an int or long
        """
        with self.assertRaises(except_orm):
            self.activity_model.update_activity(
                self.cr,
                self.uid,
                37.5
            )

    def test_id_less_than_one(self):
        """
        Test that an exception is raised if ID is less than 1
        """
        with self.assertRaises(except_orm):
            self.activity_model.update_activity(
                self.cr,
                self.uid,
                0
            )

    def test_data_model_method_called(self):
        """
        Test that the defined method on the data_model is called when the
        decorator is called
        """
        self.activity_model.update_activity(
            self.cr,
            self.uid,
            self.activity_id
        )
        self.assertTrue(self.DATA_MODEL_METHOD_CALLED)
