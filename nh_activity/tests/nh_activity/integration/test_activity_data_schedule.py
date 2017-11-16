from openerp.tests.common import TransactionCase
from openerp.osv.orm import except_orm


class TestSchedule(TransactionCase):
    """ Test the schedule method of the nh.activity model """

    def setUp(self):
        """
        Set up the tests
        """
        super(TestSchedule, self).setUp()
        self.activity_model = self.env['nh.activity']
        self.activity = self.activity_model.create(
            {
                'data_model': 'test.activity.data.model'
            }
        )

    def test_schedule(self):
        """
        Test that schedule() changes the state of the activity to scheduled
        """
        test_date = '1988-01-12 06:00:00'
        self.activity.schedule(test_date)
        self.assertEqual(
            self.activity.state,
            'scheduled',
            msg="Activity state not updated after schedule"
        )

    def test_date_scheduled(self):
        """
        Test that schedule() sets the date_scheduled property on the sheduled
        activity
        """
        test_date = '1988-01-12 06:00:00'
        self.activity.schedule(test_date)
        self.assertEqual(
            self.activity.date_scheduled,
            test_date,
            msg="Activity date_scheduled not updated after schedule"
        )

    def test_already_date_scheduled(self):
        """
        Test that schedule() moves the activity into scheduled if the activity
        already has the date_scheduled property set
        """
        test_date = '2015-10-10 12:00:00'
        self.activity.write({'date_scheduled': test_date})
        self.activity.schedule()
        self.assertEqual(
            self.activity.state,
            'scheduled',
            msg="Activity state not updated after schedule"
        )

    def test_no_date_scheduled(self):
        """
        Test that schedule() moves the activity into scheduled if the activity
        already has the date_scheduled property set
        """
        with self.assertRaises(except_orm):
            self.activity.schedule()

    def test_doesnt_change_date_scheduled(self):
        """
        Test that schedule() doesn't change the already scheduled date when
        being called on an activity with a schedule date
        :return:
        """
        test_date = '2015-10-10 12:00:00'
        self.activity.write({'date_scheduled': test_date})
        self.activity.schedule()
        self.assertEqual(
            self.activity.date_scheduled,
            test_date,
            msg="Activity date_scheduled not updated after schedule"
        )

    def test_already_started(self):
        """
        Test that when calling schedule() on an activity that is already in
        the started state that it raises an error
        """
        self.activity.write({'state': 'started'})
        with self.assertRaises(except_orm):
            self.activity.schedule()

    def test_already_completed(self):
        """
        Test that when calling schedule() on an activity that is already in
        the completed state that it raises an error
        """
        self.activity.write({'state': 'completed'})
        with self.assertRaises(except_orm):
            self.activity.schedule()

    def test_already_cancelled(self):
        """
        Test that when calling schedule() on an activity that is already in
        the cancelled state that it raises an error
        """
        self.activity.write({'state': 'cancelled'})
        with self.assertRaises(except_orm):
            self.activity.schedule()
