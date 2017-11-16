from openerp.tests.common import TransactionCase


class TestSubmitUi(TransactionCase):
    """ Test the submit_ui() method on nh.activity.data model """

    def setUp(self):
        """
        Set up the tests
        """
        super(TestSubmitUi, self).setUp()
        self.test_model = self.env['test.activity.data.model']
        self.activity_model = self.env['nh.activity']
        activity_id = self.test_model.create_activity(
            {},
            {'field1': 'test'}
        )
        self.activity = self.activity_model.browse(activity_id)

    def test_submit_ui_with_context(self):
        """
        Test submit_ui with passing the active_id in the context
        """
        test_rec = self.test_model.browse(self.activity.data_ref.id)
        response = test_rec\
            .with_context({'active_id': self.activity.id})\
            .submit_ui()
        self.assertEqual(response, {'type': 'ir.actions.act_window_close'})
        self.assertEqual(
            self.activity.data_ref,
            test_rec
        )

    def test_submit_ui_without_context(self):
        """
        Test that submit_ui without passing a context
        """
        test_rec = self.test_model.browse(self.activity.data_ref.id)
        response = test_rec.submit_ui()
        self.assertEqual(response, {'type': 'ir.actions.act_window_close'})
