# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import logging

from datetime import datetime as dt
from mock import MagicMock
from openerp.tests import common
from openerp.osv.orm import except_orm
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf
from unittest import skip

_logger = logging.getLogger(__name__)


class TestActivity(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestActivity, cls).setUpClass()
        cls.test_model_pool = cls.registry('test.activity.data.model')
        cls.activity_pool = cls.registry('nh.activity')
        cls.user_pool = cls.registry('res.users')

    def test_create_creates_an_activity(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})

        self.assertTrue(activity_id, msg="Activity create failed")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.data_model, 'test.activity.data.model',
                         msg="Activity created with the wrong data model")
        self.assertEqual(activity.summary, 'Test Activity Model',
                         msg="Activity default summary not added")
        self.assertEqual(activity.state, 'new',
                         msg="Activity default state not added")

    def test_create_raises_exception_if_no_data_model_is_passed(self):
        cr, uid = self.cr, self.uid
        with self.assertRaises(except_orm):
            self.activity_pool.create(cr, uid, {})

    def test_create_raises_exception_if_data_model_does_not_exist(self):
        cr, uid = self.cr, self.uid
        with self.assertRaises(except_orm):
            self.activity_pool.create(
                cr, uid,
                {'data_model': 'test.activity.non.existent.data.model'})

    def test_create_uses_data_model_description_if_no_summary_given(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model2'})

        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(
            activity.data_model, 'test.activity.data.model2',
            msg="Activity created with the wrong data model")
        # 'Undefined Activity' is _description of nh_activity_data
        self.assertEqual(
            activity.summary, 'Undefined Activity',
            msg="Activity default summary not added")

    def test_create_creates_activity_using_a_summary(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid,
            {
                'data_model': 'test.activity.data.model2',
                'summary': 'Test Activity Data Model'
            }
        )

        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(
            activity.data_model,
            'test.activity.data.model2',
            msg="Activity created with the wrong data model")
        self.assertEqual(
            activity.summary,
            'Test Activity Data Model', msg="Activity set summary incorrect")

    def test_create_activity_creates_activity(self):
        cr, uid = self.cr, self.uid

        activity_id = self.test_model_pool.create_activity(cr, uid, {},
                                                           {'field1': 'test'})
        self.assertTrue(activity_id,
                        msg="Create Activity from data model failed")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.data_model,
                         'test.activity.data.model',
                         msg="Create Activity set wrong data model")
        self.assertEqual(activity.create_uid.id, uid,
                         msg="Create Activity set wrong creator User")
        self.assertEqual(
            activity.data_ref.field1, 'test',
            msg="Create Activity recorded wrong data in Data Model")

    def test_create_activity_creates_activity_without_data(self):
        cr, uid = self.cr, self.uid

        activity_id = self.test_model_pool.create_activity(cr, uid, {}, {})
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertFalse(
            activity.data_ref,
            msg="Create Activity added data model object without having Data")

    def test_create_activity_raises_exception_with_wrong_param_types(self):
        cr, uid = self.cr, self.uid

        with self.assertRaises(except_orm):
            self.test_model_pool.create_activity(cr, uid, 'test', {})
        with self.assertRaises(except_orm):
            self.test_model_pool.create_activity(cr, uid, {}, 'test')

    def test_write_does_not_increment_sequence_if_state_not_changed(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        cr.execute("select coalesce(max(sequence), 0) from nh_activity")
        sequence = cr.fetchone()[0]

        self.assertTrue(self.activity_pool.write(
            cr, uid, activity_id, {'user_id': 1}), msg="Activity Write failed")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.user_id.id, 1,
                         msg="Activity not written correctly")
        self.assertNotEqual(activity.sequence, sequence+1,
                            msg="Activity sequence updated incorrectly")

    def test_write_increments_sequence_if_state_changed(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        cr.execute("select coalesce(max(sequence), 0) from nh_activity")
        sequence = cr.fetchone()[0]

        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertTrue(
            self.activity_pool.write(cr, uid, activity_id,
                                     {'state': 'started'}),
            msg="Activity Write failed")
        self.assertEqual(activity.state, 'started',
                         msg="Activity not written correctly")
        self.assertEqual(activity.sequence, sequence+1,
                         msg="Activity sequence not updated")

    def test_get_recursive_created_ids_returns_non_creator_activity_id(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        created_ids = self.activity_pool.get_recursive_created_ids(
            cr, uid, activity_id)
        self.assertEquals(activity_id, created_ids[0])

    def test_get_recursive_created_ids_returns_created_id_and_own_id(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        activity2_id = self.activity_pool.create(
            cr, uid, {'creator_id': activity_id,
                      'data_model': 'test.activity.data.model'})
        rc_ids = self.activity_pool.get_recursive_created_ids(
            cr, uid, activity_id)
        self.assertEqual(set(rc_ids), {activity_id, activity2_id})

    def test_get_recursive_created_ids_returns_ids_of_created_activities(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        activity2_id = self.activity_pool.create(
            cr, uid, {'creator_id': activity_id,
                      'data_model': 'test.activity.data.model'})
        activity3_id = self.activity_pool.create(
            cr, uid, {'creator_id': activity2_id,
                      'data_model': 'test.activity.data.model'})

        rc_ids = self.activity_pool.get_recursive_created_ids(
            cr, uid, activity_id)
        self.assertEqual(
            set(rc_ids), {activity_id, activity2_id, activity3_id})
        rc_ids = self.activity_pool.get_recursive_created_ids(
            cr, uid, activity2_id)
        self.assertEqual(set(rc_ids), {activity2_id, activity3_id})
        rc_ids = self.activity_pool.get_recursive_created_ids(
            cr, uid, activity3_id)
        self.assertEqual(set(rc_ids), {activity3_id})

    def test_update_activity_returns_True(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        self.assertTrue(
            self.activity_pool.update_activity(cr, uid, activity_id),
            msg="Event call failed")

    def test_update_returns_True_when_passed_list_of_ids(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})

        result = self.activity_pool.update_activity(cr, uid, [activity_id])
        self.assertTrue(result, msg="Event call failed")

    def test_data_model_event_raises_exception_when_passed_non_integer(self):
        cr, uid = self.cr, self.uid

        with self.assertRaises(except_orm):
            self.activity_pool.update_activity(cr, uid, 'activity ID')

    def test_data_model_event_raises_exception_when_integer_less_than_1(self):
        cr, uid = self.cr, self.uid

        with self.assertRaises(except_orm):
            self.activity_pool.update_activity(cr, uid, 0)

    def test_submit_creates_new_instance_of_data_model_if_nonexistent(self):
        # testing nh_activity_data?
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertFalse(
            activity.data_ref,
            msg="Activity Submit pre-State error: "
                "The data model already exists")
        self.assertTrue(
            self.activity_pool.submit(
                cr, uid, activity_id, {'field1': 'test'}),
            msg="Activity Submit failed")

        # TODO: test for _get_data_type_selection
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertTrue(
            activity.data_ref,
            msg="Activity Data Model not created after submit")
        self.assertEqual(
            activity.data_ref._name,
            'test.activity.data.model', msg="Wrong Data Model created")
        self.assertEqual(
            activity.data_ref.field1,
            'test', msg="Data Model data not submitted")

    def test_submit_updates_data_on_an_existent_data_model(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        self.assertTrue(
            self.activity_pool.submit(
                cr, uid, activity_id, {'field1': 'test'}),
            msg="Activity Submit failed")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.data_ref.field1, 'test',
                         msg="Data Model data not submitted")

    def test_submit_raises_exception_on_non_dict_type(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        with self.assertRaises(except_orm):
            self.activity_pool.submit(cr, uid, activity_id, 'test3')

    def test_submit_raises_except_on_completed_and_cancelled_activities(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})

        self.activity_pool.write(cr, uid, activity_id, {'state': 'completed'})
        with self.assertRaises(except_orm):
            self.activity_pool.submit(
                cr, uid, activity_id, {'field1': 'test4'})
        self.activity_pool.write(cr, uid, activity_id, {'state': 'cancelled'})
        with self.assertRaises(except_orm):
            self.activity_pool.submit(
                cr, uid, activity_id, {'field1': 'test4'})

    def test_schedule_schedules_an_activity(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        test_date = [
            '2015-10-10 12:00:00',
            dt(year=2015, month=10, day=10, hour=13, minute=0, second=0),
            '2015-10-09 12:00',
            '2015-10-07']
        self.assertTrue(
            self.activity_pool.schedule(cr, uid, activity_id, test_date[0]),
            msg="Activity Schedule failed")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.state, 'scheduled',
                         msg="Activity state not updated after schedule")
        self.assertEqual(
            activity.date_scheduled, test_date[0],
            msg="Activity date_scheduled not updated after schedule")

    def test_schedule_raises_except_when_bad_formatted_scheduled_date(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        with self.assertRaises(except_orm):
            self.activity_pool.schedule(cr, uid, activity_id, 2015)
        with self.assertRaises(except_orm):
            self.activity_pool.schedule(cr, uid, activity_id, 'Not A Date')

    def test_schedule_schedules_activity_when_already_date_scheduled(self):
        cr, uid = self.cr, self.uid
        test_date = '2015-10-10 12:00:00'
        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})

        self.activity_pool.write(
            cr, uid, activity_id, {'date_scheduled': test_date})

        self.assertTrue(self.activity_pool.schedule(cr, uid, activity_id),
                        msg="Activity Schedule failed")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.state, 'scheduled',
                         msg="Activity state not updated after schedule")
        self.assertEqual(
            activity.date_scheduled, test_date,
            msg="Activity date_scheduled not updated after schedule")

    def test_schedule_raises_exception_when_scheduled_without_date(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        with self.assertRaises(except_orm):
            self.activity_pool.schedule(cr, uid, activity_id)

    def test_schedule_with_datetime(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        test_date = dt(year=2015, month=10, day=10, hour=13, minute=0,
                       second=0)

        self.assertTrue(
            self.activity_pool.schedule(cr, uid, activity_id, test_date),
            msg="Activity Schedule failed")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(
            activity.date_scheduled,
            '2015-10-10 13:00:00',
            msg="Activity date_scheduled not updated after schedule")

    def test_schedule_activity_with_different_date_formats(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        test_date_1 = '2015-10-09 12:00'
        test_date_2 = '2015-10-07'

        self.assertTrue(self.activity_pool.schedule(
            cr, uid, activity_id, test_date_1), msg="Activity Schedule failed")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(
            activity.date_scheduled, '2015-10-09 12:00:00',
            msg="Activity date_scheduled not updated after schedule")
        self.assertTrue(self.activity_pool.schedule(
            cr, uid, activity_id, test_date_2), msg="Activity Schedule failed")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(
            activity.date_scheduled,
            '2015-10-07 00:00:00',
            msg="Activity date_scheduled not updated after schedule")

    def test_schedule_dont_schedule_activity_started_completed_cancelled(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        self.activity_pool.write(cr, uid, activity_id, {'state': 'started'})
        activity2_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        self.activity_pool.write(cr, uid, activity2_id, {'state': 'completed'})
        activity3_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        self.activity_pool.write(cr, uid, activity3_id, {'state': 'completed'})

        with self.assertRaises(except_orm):
            self.activity_pool.schedule(cr, uid, activity_id)
        with self.assertRaises(except_orm):
            self.activity_pool.schedule(cr, uid, activity2_id)
        with self.assertRaises(except_orm):
            self.activity_pool.schedule(cr, uid, activity3_id)

    def test_assign_an_activity_to_user(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        self.assertTrue(self.activity_pool.assign(cr, uid, activity_id, uid),
                        msg="Assign Activity failed")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.user_id.id, uid,
                         msg="User id not updated after Assign")

    def test_assign_raises_except_when_assign_already_assigned_activity(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        self.activity_pool.assign(cr, uid, activity_id, uid)
        user_ids = self.user_pool.search(cr, uid, [['id', '!=', uid]])
        with self.assertRaises(except_orm):
            self.activity_pool.assign(cr, uid, activity_id, user_ids[0])

    def test_assign_raises_exception_when_sending_wrong_user_id_argument(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        self.activity_pool.write(cr, uid, activity_id, {'user_id': False})
        with self.assertRaises(except_orm):
            self.activity_pool.assign(cr, uid, activity_id, 'User ID')

    def test_assign_raise_except_when_assign_activity_complete_cancelled(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        self.activity_pool.write(cr, uid, activity_id, {'state': 'completed'})
        with self.assertRaises(except_orm):
            self.activity_pool.assign(cr, uid, activity_id, uid)
        self.activity_pool.write(cr, uid, activity_id, {'state': 'cancelled'})
        with self.assertRaises(except_orm):
            self.activity_pool.assign(cr, uid, activity_id, uid)

    def test_assign_an_activity_already_assigned(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        self.assertTrue(self.activity_pool.assign(
            cr, uid, activity_id, uid), msg="Assign Activity Failed")
        self.activity_pool.assign(cr, uid, activity_id, uid)
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEquals(activity.assign_locked, True)

    def test_unassign_unassigns_an_activity_from_user(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid,
            {'user_id': uid, 'data_model': 'test.activity.data.model'})
        self.assertTrue(self.activity_pool.unassign(cr, uid, activity_id),
                        msg="Activity Unassign failed")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertFalse(activity.user_id,
                         msg="Activity not unassigned after Unassign")

    def test_unassign_raises_exception_when_no_user_id_passed(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        with self.assertRaises(except_orm):
            self.activity_pool.unassign(cr, uid, activity_id)

    def test_unassign_raises_exception_when_no_user_is_assigned(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        user_ids = self.user_pool.search(cr, uid, [['id', '!=', uid]])
        self.activity_pool.write(
            cr, uid, activity_id, {'user_id': user_ids[0]})
        with self.assertRaises(except_orm):
            self.activity_pool.unassign(cr, uid, activity_id)

    def test_unassign_raises_except_when_activity_is_completed_cancelled(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        self.activity_pool.write(
            cr, uid, activity_id, {'state': 'completed', 'user_id': uid})
        with self.assertRaises(except_orm):
            self.activity_pool.unassign(cr, uid, activity_id)
        self.activity_pool.write(cr, uid, activity_id, {'state': 'cancelled'})
        with self.assertRaises(except_orm):
            self.activity_pool.unassign(cr, uid, activity_id)

    def test_unassign_locked_activity(self):
        cr, uid = self.cr, self.uid
        self.activity_pool.write = MagicMock()

        activity_id = self.activity_pool.create(
            cr, uid,
            {
                'user_id': uid, 'data_model': 'test.activity.data.model',
                'assign_locked': True
            }
        )
        self.activity_pool.unassign(cr, uid, activity_id)
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertTrue(activity.assign_locked)
        self.assertFalse(self.activity_pool.write.called)
        del self.activity_pool.write

    @skip('Fix the "almost-equal comparison" for datetime')
    def test_start_starts_an_activity(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        self.assertTrue(self.activity_pool.start(
            cr, uid, activity_id), msg="Activity Start failed")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.state, 'started',
                         msg="Activity state not updated after Start")
        self.assertAlmostEqual(
            activity.date_started, dt.now().strftime(dtf),
            msg="Activity date started not updated after Start")

    def test_start_raises_exception_when_started_completed_cancelled(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        self.assertTrue(self.activity_pool.start(cr, uid, activity_id),
                        msg="Activity Start failed")

        with self.assertRaises(except_orm):
            self.activity_pool.start(cr, uid, activity_id)
        self.activity_pool.write(cr, uid, activity_id, {'state': 'completed'})
        with self.assertRaises(except_orm):
            self.activity_pool.start(cr, uid, activity_id)
        self.activity_pool.write(cr, uid, activity_id, {'state': 'cancelled'})
        with self.assertRaises(except_orm):
            self.activity_pool.start(cr, uid, activity_id)

    @skip('Fix the "almost-equal comparison" for datetime')
    def test_complete_completes_an_activity(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        self.assertTrue(self.activity_pool.complete(
            cr, uid, activity_id), msg="Activity Complete failed")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.state, 'completed',
                         msg="Activity state not updated after Complete")
        self.assertAlmostEqual(
            activity.date_terminated, dt.now().strftime(dtf),
            msg="Activity date terminated not updated after Complete")
        self.assertEqual(
            activity.terminate_uid.id, uid,
            msg="Activity completion user not updated after Complete")

    def test_complete_raises_exception_when_completed_cancelled(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        self.activity_pool.write(cr, uid, activity_id, {'state': 'completed'})
        with self.assertRaises(except_orm):
            self.activity_pool.complete(cr, uid, activity_id)
        self.activity_pool.write(cr, uid, activity_id, {'state': 'cancelled'})
        with self.assertRaises(except_orm):
            self.activity_pool.complete(cr, uid, activity_id)

    @skip('Fix the "almost-equal comparison" for datetime')
    def test_cancel_cancels_an_activity(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        self.assertTrue(self.activity_pool.cancel(cr, uid, activity_id),
                        msg="Activity Cancel failed")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.state, 'cancelled',
                         msg="Activity state not updated after Cancel")
        self.assertAlmostEqual(
            activity.date_terminated, dt.now().strftime(dtf),
            msg="Activity date terminated not updated after Cancel")
        self.assertEqual(
            activity.terminate_uid.id, uid,
            msg="Activity completion user not updated after Cancel")

    def test_cancel_raises_exception_when_cancelled_completed(self):
        cr, uid = self.cr, self.uid

        activity_id = self.activity_pool.create(
            cr, uid, {'data_model': 'test.activity.data.model'})
        self.activity_pool.write(cr, uid, activity_id, {'state': 'cancelled'})
        with self.assertRaises(except_orm):
            self.activity_pool.cancel(cr, uid, activity_id)

    def test_is_action_allowed_when_action_is_schedule(self):
        self.assertTrue(self.test_model_pool.is_action_allowed('new',
                                                               'schedule'))
        self.assertTrue(self.test_model_pool.is_action_allowed('scheduled',
                                                               'schedule'))
        self.assertFalse(self.test_model_pool.is_action_allowed('started',
                                                                'schedule'))
        self.assertFalse(self.test_model_pool.is_action_allowed('completed',
                                                                'schedule'))
        self.assertFalse(self.test_model_pool.is_action_allowed('cancelled',
                                                                'schedule'))

    def test_is_action_allowed_when_action_is_start(self):
        self.assertTrue(self.test_model_pool.is_action_allowed('new',
                                                               'start'))
        self.assertTrue(self.test_model_pool.is_action_allowed('scheduled',
                                                               'start'))
        self.assertFalse(self.test_model_pool.is_action_allowed('started',
                                                                'start'))
        self.assertFalse(self.test_model_pool.is_action_allowed('completed',
                                                                'start'))
        self.assertFalse(self.test_model_pool.is_action_allowed('cancelled',
                                                                'start'))

    def test_is_action_allowed_when_action_is_completed(self):
        self.assertTrue(self.test_model_pool.is_action_allowed('new',
                                                               'complete'))
        self.assertTrue(self.test_model_pool.is_action_allowed('scheduled',
                                                               'complete'))
        self.assertTrue(self.test_model_pool.is_action_allowed('started',
                                                               'complete'))
        self.assertFalse(self.test_model_pool.is_action_allowed('completed',
                                                                'complete'))
        self.assertFalse(self.test_model_pool.is_action_allowed('cancelled',
                                                                'complete'))

    def test_is_action_allowed_when_action_is_cancel(self):
        self.assertTrue(self.test_model_pool.is_action_allowed('new',
                                                               'cancel'))
        self.assertTrue(self.test_model_pool.is_action_allowed('scheduled',
                                                               'cancel'))
        self.assertTrue(self.test_model_pool.is_action_allowed('started',
                                                               'cancel'))
        self.assertTrue(self.test_model_pool.is_action_allowed('completed',
                                                               'cancel'))
        self.assertFalse(self.test_model_pool.is_action_allowed('cancelled',
                                                                'cancel'))

    def test_is_action_allowed_when_action_is_submit(self):
        self.assertTrue(self.test_model_pool.is_action_allowed('new',
                                                               'submit'))
        self.assertTrue(self.test_model_pool.is_action_allowed('scheduled',
                                                               'submit'))
        self.assertTrue(self.test_model_pool.is_action_allowed('started',
                                                               'submit'))
        self.assertFalse(self.test_model_pool.is_action_allowed('completed',
                                                                'submit'))
        self.assertFalse(self.test_model_pool.is_action_allowed('cancelled',
                                                                'submit'))

    def test_is_action_allowed_when_action_is_assign(self):
        self.assertTrue(self.test_model_pool.is_action_allowed('new',
                                                               'assign'))
        self.assertTrue(self.test_model_pool.is_action_allowed('scheduled',
                                                               'assign'))
        self.assertTrue(self.test_model_pool.is_action_allowed('started',
                                                               'assign'))
        self.assertFalse(self.test_model_pool.is_action_allowed('completed',
                                                                'assign'))
        self.assertFalse(self.test_model_pool.is_action_allowed('cancelled',
                                                                'assign'))

    def test_is_action_allowed_when_action_is_unassign(self):
        self.assertTrue(self.test_model_pool.is_action_allowed('new',
                                                               'unassign'))
        self.assertTrue(self.test_model_pool.is_action_allowed('scheduled',
                                                               'unassign'))
        self.assertTrue(self.test_model_pool.is_action_allowed('started',
                                                               'unassign'))
        self.assertFalse(self.test_model_pool.is_action_allowed('completed',
                                                                'unassign'))
        self.assertFalse(self.test_model_pool.is_action_allowed('cancelled',
                                                                'unassign'))

    def test_check_action_schedule_returns_True_from_state_new_scheduled(self):
        self.assertTrue(self.test_model_pool.check_action('new', 'schedule'))
        self.assertTrue(self.test_model_pool.check_action('scheduled',
                                                          'schedule'))

    def test_schedule_raises_except_from_state_started_completed_cancel(self):
        """
        Test check_action "schedule" raises an exception
        when triggered from states:
         - started
         - completed
         - cancelled
        """
        with self.assertRaises(except_orm):
            self.test_model_pool.check_action('started', 'schedule')
        with self.assertRaises(except_orm):
            self.test_model_pool.check_action('completed', 'schedule')
        with self.assertRaises(except_orm):
            self.test_model_pool.check_action('cancelled', 'schedule')

    def test_check_action_start_returns_True_from_state_new_scheduled(self):
        self.assertTrue(self.test_model_pool.check_action('new', 'start'))
        self.assertTrue(self.test_model_pool.check_action('scheduled',
                                                          'start'))

    def test_start_raises_except_from_state_started_completed_cancelled(self):
        """
        Test check_action "start" raises an exception
        when triggered from states:
         - started
         - completed
         - cancelled
        """
        with self.assertRaises(except_orm):
            self.test_model_pool.check_action('started', 'start')
        with self.assertRaises(except_orm):
            self.test_model_pool.check_action('completed', 'start')
        with self.assertRaises(except_orm):
            self.test_model_pool.check_action('cancelled', 'start')

    def test_complete_returns_True_from_state_new_scheduled_started(self):
        """
        Test check_action "complete" returns boolean ``True``
        when triggered from states:
         - new
         - scheduled
         - started
        """
        self.assertTrue(self.test_model_pool.check_action('new', 'complete'))
        self.assertTrue(self.test_model_pool.check_action('scheduled',
                                                          'complete'))
        self.assertTrue(self.test_model_pool.check_action('started',
                                                          'complete'))

    def test_complete_raises_exception_from_state_completed_cancelled(self):
        """
        Test check_action "complete" raises an exception
        when triggered from states:
         - completed
         - cancelled
        """
        with self.assertRaises(except_orm):
            self.test_model_pool.check_action('completed', 'complete')
        with self.assertRaises(except_orm):
            self.test_model_pool.check_action('cancelled', 'complete')

    def test_check_action_cancel_returns_True_from_state_new_scheduled(self):
        self.assertTrue(self.test_model_pool.check_action('new', 'cancel'))
        self.assertTrue(self.test_model_pool.check_action('scheduled',
                                                          'cancel'))

    def test_cancel_returns_True_from_state_started_completed(self):
        """
        Test check_action "cancel" returns boolean ``True``
        when triggered from states:
         - started
         - completed
        """
        self.assertTrue(self.test_model_pool.check_action('started', 'cancel'))
        self.assertTrue(self.test_model_pool.check_action('completed',
                                                          'cancel'))

    def test_cancel_raises_exception_from_state_cancelled(self):
        with self.assertRaises(except_orm):
            self.test_model_pool.check_action('cancelled', 'cancel')

    def test_submit_returns_True_from_state_new_scheduled_started(self):
        self.assertTrue(self.test_model_pool.check_action('new', 'submit'))
        self.assertTrue(self.test_model_pool.check_action('scheduled',
                                                          'submit'))
        self.assertTrue(self.test_model_pool.check_action('started', 'submit'))

    def test_submit_raises_exception_from_state_completed_cancelled(self):
        """
        Test check_action "submit" raises an exception
        when triggered from states:
         - completed
         - cancelled
        """
        with self.assertRaises(except_orm):
            self.test_model_pool.check_action('completed', 'submit')
        with self.assertRaises(except_orm):
            self.test_model_pool.check_action('cancelled', 'submit')

    def test_check_action_assign_returns_True_from_new_scheduled_started(self):
        self.assertTrue(self.test_model_pool.check_action('new', 'assign'))
        self.assertTrue(self.test_model_pool.check_action('scheduled',
                                                          'assign'))
        self.assertTrue(self.test_model_pool.check_action('started', 'assign'))

    def test_assign_raises_exception_from_completed_cancelled(self):
        """
        Test check_action "assign" raises an exception
        when triggered from states:
         - completed
         - cancelled
        """
        with self.assertRaises(except_orm):
            self.test_model_pool.check_action('completed', 'assign')
        with self.assertRaises(except_orm):
            self.test_model_pool.check_action('cancelled', 'assign')

    def test_unassign_returns_True_from_new_scheduled_started(self):
        """
        Test check_action "unassign" returns boolean ``True``
        when triggered from states:
         - new
         - scheduled
         - started
        """
        self.assertTrue(self.test_model_pool.check_action('new', 'unassign'))
        self.assertTrue(self.test_model_pool.check_action('scheduled',
                                                          'unassign'))
        self.assertTrue(self.test_model_pool.check_action('started',
                                                          'unassign'))

    def test_unassign_raises_exception_from_completed_cancelled(self):
        """
        Test check_action "unassign" raises an exception
        when triggered from states:
         - completed
         - cancelled
        """
        with self.assertRaises(except_orm):
            self.test_model_pool.check_action('completed', 'unassign')
        with self.assertRaises(except_orm):
            self.test_model_pool.check_action('cancelled', 'unassign')

    def test_submit_ui_submit_with_and_or_without_context_arg(self):
        cr, uid = self.cr, self.uid

        activity_id = self.test_model_pool.create_activity(cr, uid, {},
                                                           {'field1': 'test'})
        activity = self.activity_pool.browse(cr, uid, activity_id)
        # with context
        self.test_model_pool.submit_ui(cr, uid, [activity.data_ref.id],
                                       context={'active_id': activity_id})

        # without context
        self.test_model_pool.submit_ui(cr, uid, [activity.data_ref.id])

    def test_complete_ui_completes_activity_with_or_without_context_arg(self):
        cr, uid = self.cr, self.uid

        activity_id = self.test_model_pool.create_activity(cr, uid, {},
                                                           {'field1': 'test'})
        activity = self.activity_pool.browse(cr, uid, activity_id)
        # with context
        self.test_model_pool.complete_ui(cr, uid, [activity.data_ref.id],
                                         context={'active_id': activity_id})
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(activity.state, 'completed')

        # without context
        self.test_model_pool.complete_ui(cr, uid, [activity.data_ref.id])
