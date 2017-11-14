from openerp.tests.common import TransactionCase


class TestSubmit(TransactionCase):
    """
    Test the submit() method of the nh_activity model
    """

    EVENT_TRIGGERED = None

    def setUp(self):
        """
        Set up the tests
        """
        super(TestSubmit, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.EVENT_TRIGGERED = None

        def patch_data_model_event(*args, **kwargs):
            self.EVENT_TRIGGERED = kwargs.get('callback')
            return True

        self.activity_model._patch_method(
            'data_model_event',
            patch_data_model_event
        )

        activity_id = self.activity_pool.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )
        self.activity = self.activity_pool.browse(activity_id)

    def tearDown(self):
        """
        Remove any patches set up as part of the tests
        """
        self.activity_model._revert_method('data_model_event')
        super(TestSubmit, self).tearDown()

    def test_creates_new_data_ref(self):
        """
        Test that if the activity is created with no data model instance that
        it creates a new instance on submission
        """
        self.activity.submit({'field1': 'test'})
        self.assertTrue(
            activity.data_ref,
            msg="Activity Data Model not created after submit")
        self.assertEqual(
            activity.data_ref._name,
            'test.activity.data.model',
            msg="Wrong Data Model created"
        )

    def test_sets_field_on_submit(self):
        """
        Test that the field that is submitted is set on the created data_ref
        """
        self.activity.submit({'field1': 'test'})
        self.assertEqual(
            activity.data_ref.field1,
            'test',
            msg="Data Model data not submitted"
        )

    def test_updates_data_ref(self):
        """
        Test that is the activity already has a data_ref that it updates that
        data_ref and doesn't create a new instance
        """
        self.activity.submit({'field1': 'test'})
        self.activity.submit({'field1': 'test2'})
        self.assertEqual(
            self.activity.data_ref.field1,
            'test2',
            msg="Data Model data not submitted"
        )

    def test_submit_non_dict(self):
        """
        Test that an exception is raised when passed a non-dictionary type
        """
        with self.assertRaises(except_orm):
            self.activity.submit(activity_id, 'test3')

    def test_submit_completed(self):
        """
        Test that on trying to submit a completed or cancelled activity it
        raises an exception
        """
        self.activity.write({'state': 'completed'})
        with self.assertRaises(except_orm):
            self.activity.submit({'field1': 'test4'})

    def test_submit_cancelled(self):
        """
        Test that on trying to submit a cancelled activity it raises an
        exception
        """
        self.activity.write({'state': 'cancelled'})
        with self.assertRaises(except_orm):
            self.activity.submit({'field1': 'test4'})

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
            'submit',
            msg="Event call failed"
        )
