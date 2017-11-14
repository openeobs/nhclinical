from openerp.tests.common import TransactionCase


class TestCreateActivity(TransactionCase):
    """ Test the create_activity() method of the activity model """
    
    def setUp(self):
        """ Set up the tests """
        super(TestCreateActivity, self).setUp()
        self.test_model = self.env['test.activity.data.model']
        self.activity_model = self.env['nh.activity']
        self.user_model = self.env['res.users']
        
    def test_create_activity(self):
        """
        Test the create_activity method creates an activity
        """
        activity_id = self.test_model.create_activity(
            {},
            {
                'field1': 'test'
            }
        )
        self.assertTrue(activity_id,
                        msg="Create Activity from data model failed")
        
    def test_data_model(self):
        """
        Test that create_activity sets the data_model
        """
        activity_id = self.test_model.create_activity(
            {},
            {
                'field1': 'test'
            }
        )
        activity = self.activity_model.browse(activity_id)
        self.assertEqual(
            activity.data_model,
            'test.activity.data.model',
            msg="Create Activity set wrong data model"
        )
        
    def test_create_uid(self):
        """ 
        Test that create_activity sets the user who created the activity 
        """
        activity_id = self.test_model.create_activity(
            {},
            {
                'field1': 'test'
            }
        )
        activity = self.activity_model.browse(activity_id)
        self.assertEqual(activity.create_uid.id, uid,
                         msg="Create Activity set wrong creator User")

    def test_model_field_value(self):
        """
        Test that the field value supplied during create_activity sets the
        field value on the model instance created as part of create_activity
        """
        activity_id = self.test_model.create_activity(
            {},
            {
                'field1': 'test'
            }
        )
        activity = self.activity_model.browse(activity_id)
        self.assertEqual(
            activity.data_ref.field1,
            'test',
            msg="Create Activity recorded wrong data in Data Model"
        )

    def test_no_data(self):
        """
        Test that create_activity does not create a data_ref if no data is
        supplied
        """
        activity_id = self.test_model.create_activity({}, {})
        activity = self.activity_model.browse(activity_id)
        self.assertFalse(
            activity.data_ref,
            msg="Create Activity added data model object without having Data"
        )

    def test_wrong_activity_data(self):
        """
        Test create_activity raises an exception if don't pass a dictionary
        for the activity data
        """
        with self.assertRaises(except_orm):
            self.test_model.create_activity('test', {})

    def test_wrong_data_ref_data(self):
        """
        Test create_activity raises an exception if don't pass a dictionary
        for the data_ref data
        """
        with self.assertRaises(except_orm):
            self.test_model.create_activity({}, 'test')
