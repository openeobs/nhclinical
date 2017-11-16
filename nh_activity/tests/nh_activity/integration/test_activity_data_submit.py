from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestActivityDataSubmit(TransactionCase):
    """
    Test the submit() method of the nh_activity model
    """

    def setUp(self):
        """
        Set up the tests
        """
        super(TestActivityDataSubmit, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.activity = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )

    def test_creates_new_data_ref(self):
        """
        Test that if the activity is created with no data model instance that
        it creates a new instance on submission
        """
        self.activity.submit({'field1': 'test'})
        self.assertEqual(
            self.activity.data_ref._name,
            'test.activity.data.model',
            msg="Wrong Data Model created"
        )

    def test_sets_field_on_submit(self):
        """
        Test that the field that is submitted is set on the created data_ref
        """
        self.activity.submit({'field1': 'test'})
        self.assertEqual(
            self.activity.data_ref.field1,
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
