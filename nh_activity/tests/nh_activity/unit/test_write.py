from openerp.tests.common import TransactionCase


class TestActivityWrite(TransactionCase):
    """ Test the write() method of nh_activity model """

    def setUp(self):
        """ Set up the tests """
        super(TestActivityWrite, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.user_model = self.env['res.users']
        self.activity = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )

    def test_write(self):
        """
        Test that write updates the data of the activity.
        """
        self.activity.write(
            {
                'user_id': 1
            }
        )
        self.assertEqual(
            self.activity.user_id.id,
            1,
            msg="Activity not written correctly"
        )

    def test_state_not_changed(self):
        """
        Test that the sequence is not incremented if the state doesn't change
        """
        self.activity.start()
        self.cr.execute(
            "select coalesce(max(sequence), 0) from nh_activity")
        sequence = self.cr.fetchone()[0]
        self.activity.write(
            {
                'user_id': 1
            }
        )
        self.assertEqual(
            self.activity.sequence,
            sequence,
            msg="Activity sequence updated incorrectly"
        )

    def test_state_changed(self):
        """
        Test that the sequence is incremented if the state is changed.
        """
        self.activity.start()
        self.cr.execute("select coalesce(max(sequence), 0) from nh_activity")
        sequence = self.cr.fetchone()[0]
        self.activity.write(
            {
                'state': 'started'
            }
        )
        self.assertEqual(
            self.activity.sequence,
            sequence+1,
            msg="Activity sequence not updated"
        )
