from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestCreate(TransactionCase):
    """ Test the create method of the nh.activity model """

    def setUp(self):
        """
        Set up the tests
        """
        super(TestCreate, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.user_model = self.env['res.users']

    def test_create(self):
        """
        Test that create() creates an activity
        """
        activity_id = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )
        self.assertTrue(activity_id, msg="Activity create failed")

    def test_create_data_model(self):
        """
        Test that create() method correctly sets the data model for the created
        activity
        """
        activity = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )
        self.assertEqual(
            activity.data_model,
            'test.activity.data.model',
            msg="Activity created with the wrong data model"
        )

    def test_create_summary(self):
        """
        Test that the create() method correctly sets the summary for the
        created activity
        """
        activity = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )
        self.assertEqual(
            activity.summary,
            'Test Activity Model',
            msg="Activity default summary not added"
        )

    def test_create_state(self):
        """
        Test that the create() method correctly sets the initial state of the
        created activity
        """
        activity = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )
        self.assertEqual(
            activity.state,
            'new',
            msg="Activity default state not added"
        )

    def test_no_data_model(self):
        """
        Test that the create() method raises an error when no data_model
        is defined
        """
        with self.assertRaises(except_orm):
            self.activity_model.create({})

    def test_data_model_doesnt_exist(self):
        """
        Test that the create() method raises an error when the data_model
        does not exist
        """
        with self.assertRaises(except_orm):
            self.activity_model.create(
                {
                    'data_model': 'test.activity.non.existent.data.model'
                }
            )

    def test_data_model_desc_for_summary(self):
        """
        Test that the created activity will have the summary defined on the
        data model if the data model has a description
        """

        activity = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model2'
            }
        )
        self.assertEqual(
            activity.summary,
            'Undefined Activity',
            msg="Activity default summary not added"
        )

    def test_create_using_a_summary(self):
        """
        Test that when a summary is supplied that the created activity has that
        summary
        """
        activity = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model2',
                'summary': 'Test Activity Data Model'
            }
        )
        self.assertEqual(
            activity.summary,
            'Test Activity Data Model',
            msg="Activity set summary incorrect"
        )
