from openerp.tests.common import TransactionCase


class TestSubmitUi(TransactionCase):
    """ Test the submit_ui() method on nh.activity.data model """

    def setUp(self):
        """
        Set up the tests
        """
        super(TestSubmit, self).setUp()
        self.test_model = self.env['test.activity.data.model']
        activity_id = self.test_model_pool.create_activity(
            {}, {'field1': 'test'})
        self.activity = self.activity_pool.browse(activity_id)

    def test_submit_ui_with_context(self):
        """
        Test submit_ui with passing the active_id in the context
        """
        response = self.test_model_pool\
            .with_content({'active_id': self.activity.id})\
            .submit_ui([self.activity.data_ref.id])
        self.assertEqual(response, {'type': 'ir.actions.act_window_close'})
        self.assertEqual(
            self.activity.data_ref,
            'test.activity.data.model,{}'.format(activity.data_ref.id)
        )

    def test_submit_ui_without_context(self):
        """
        Test that submit_ui without passing a context
        """
        response = self.test_model_pool\
            .submit_ui([self.activity.data_ref.id])
        self.assertEqual(response, {'type': 'ir.actions.act_window_close'})
