from openerp.tests.common import TransactionCase


class TestActivityWrite(TransactionCase):
    """ Test the write() method of nh_activity model """

    def setUp(self):
        """ Set up the tests """
        super(TestActivityWrite, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.user_model = self.env['res.users']

    def test_write(self):
        """
        Test that write updates the data of the activity
        """
        self.activity_model.write(
            activity_id,
            {
                'user_id': 1
            }
        )
        activity = self.activity_model.browse(activity_id)
        self.assertEqual(
            activity.user_id.id,
            1,
            msg="Activity not written correctly"
        )

    def test_state_not_changed(self):
        """
        Test that the sequence is not incremented if the state doesn't change
        """
        activity_id = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )
        self.cr.execute("select coalesce(max(sequence), 0) from nh_activity")
        sequence = self.cr.fetchone()[0]
        self.activity_model.write(
            activity_id,
            {
                'user_id': 1
            }
        )
        activity = self.activity_model.browse(activity_id)
        self.assertEqual(
            activity.sequence,
            sequence,
            msg="Activity sequence updated incorrectly"
        )

    def test_state_changed(self):
        """
        Test that the sequence is incrememted if the state is changed
        """
        activity_id = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )
        self.cr.execute("select coalesce(max(sequence), 0) from nh_activity")
        sequence = self.cr.fetchone()[0]
        activity = self.activity_model.browse(activity_id)
        self.activity_model.write(
            activity_id,
            {
                'state': 'started'
            }
        )
        self.assertEqual(
            activity.sequence,
            sequence+1,
            msg="Activity sequence not updated"
        )
