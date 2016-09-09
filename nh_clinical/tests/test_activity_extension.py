# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
from openerp.tests import common
from datetime import datetime as dt
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf

from faker import Faker
fake = Faker()


class TestActivityExtension(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestActivityExtension, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.users_pool = cls.registry('res.users')
        cls.groups_pool = cls.registry('res.groups')
        cls.activity_pool = cls.registry('nh.activity')
        cls.patient_pool = cls.registry('nh.clinical.patient')
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.context_pool = cls.registry('nh.clinical.context')
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.spell_pool = cls.registry('nh.clinical.spell')
        cls.test_pool = cls.registry('test.activity.data.model0')
        cls.test2_pool = cls.registry('test.activity.data.model1')
        cls.test3_pool = cls.registry('test.activity.data.model3')

        cls.apidemo = cls.registry('nh.clinical.api.demo')

        cls.patient_ids = cls.apidemo.build_unit_test_env1(cr, uid,
                                                           bed_count=4,
                                                           patient_count=4)

        cls.wu_id = cls.location_pool.search(cr, uid, [('code', '=', 'U')])[0]
        cls.wt_id = cls.location_pool.search(cr, uid, [('code', '=', 'T')])[0]
        cls.pos_id = cls.location_pool.read(
            cr, uid, cls.wu_id, ['pos_id'])['pos_id'][0]
        cls.pos_location_id = cls.pos_pool.read(
            cr, uid, cls.pos_id, ['location_id'])['location_id'][0]

        cls.wmu_id = cls.users_pool.search(cr, uid, [('login', '=', 'WMU')])[0]
        cls.wmt_id = cls.users_pool.search(cr, uid, [('login', '=', 'WMT')])[0]
        cls.nu_id = cls.users_pool.search(cr, uid, [('login', '=', 'NU')])[0]
        cls.nt_id = cls.users_pool.search(cr, uid, [('login', '=', 'NT')])[0]
        cls.adt_id = cls.users_pool.search(cr, uid,
                                           [('groups_id.name',
                                             'in',
                                             ['NH Clinical ADT Group']),
                                            ('pos_id', '=', cls.pos_id)])[0]

        patient_id = fake.random_element(cls.patient_ids)
        patient2_id = fake.random_element(cls.patient_ids)
        while patient2_id == patient_id:
            patient2_id = fake.random_element(cls.patient_ids)
        code = str(fake.random_int(min=1000001, max=9999999))
        code2 = str(fake.random_int(min=100001, max=999999))
        spell_data = {
            'patient_id': patient_id,
            'pos_id': cls.pos_id,
            'code': code,
            'start_date': dt.now().strftime(dtf)}
        spell2_data = {
            'patient_id': patient2_id,
            'pos_id': cls.pos_id,
            'code': code2,
            'start_date': dt.now().strftime(dtf)}
        spell_activity_id = cls.spell_pool.create_activity(cr, uid, {},
                                                           spell_data)
        cls.activity_pool.start(cr, uid, spell_activity_id)
        cls.spell_id = spell_activity_id
        spell_activity_id = cls.spell_pool.create_activity(cr, uid, {},
                                                           spell2_data)
        cls.activity_pool.start(cr, uid, spell_activity_id)
        cls.spell2_id = spell_activity_id
        cls.patient_id = patient_id
        cls.patient2_id = patient2_id
        cls.context_id = cls.context_pool.create(
            cr, uid, {'name': 'test', 'models': "['nh.clinical.location']"})
        cls.location_pool.write(cr, uid, cls.wu_id,
                                {'context_ids': [[6, 0, [cls.context_id]]]})

    def test_01_audit_shift_coordinator(self):
        cr, uid = self.cr, self.uid

        self.assertFalse(self.spell_pool._audit_shift_coordinator(
            cr, uid, self.spell_id),
            msg="Audit Shift Coordinator should return False "
                "when the activity has no location")
        # try to write without data
        self.assertTrue(self.activity_pool.write(
            cr, uid, self.spell_id, False), msg="Error on activity write")
        # include location_id in data
        self.assertTrue(self.activity_pool.write(cr, uid, self.spell_id,
                                                 {'location_id': self.wu_id}))
        self.assertTrue(self.spell_pool._audit_shift_coordinator(
            cr, uid, [self.spell_id]), msg="Audit Shift Coordinator failed")
        spell = self.activity_pool.browse(cr, uid, self.spell_id)
        self.assertEqual(
            spell.ward_manager_id.id,
            self.wmu_id,
            msg="Audit Shift Coordinator recorded the wrong user id"
        )
        self.activity_pool.write(cr, uid, self.spell_id,
                                 {'location_id': self.wt_id})
        self.activity_pool.complete(cr, uid, self.spell_id)
        spell = self.activity_pool.browse(cr, uid, self.spell_id)
        self.assertEqual(spell.ward_manager_id.id, self.wmt_id,
                         msg="Audit Shift Coordinator failed or "
                             "recorded the wrong user id on Complete")

    def test_02_cancel_open_activities(self):
        cr, uid = self.cr, self.uid

        activity_id = self.test_pool.create_activity(
            cr, uid, {'parent_id': self.spell2_id}, {})
        self.assertTrue(self.activity_pool.cancel_open_activities(
            cr, uid, self.spell2_id, 'test.activity.data.model0'))
        self.assertEqual(self.activity_pool.read(
            cr, uid, activity_id, ['state'])['state'], 'cancelled')

    def test_03_update_users(self):
        cr, uid = self.cr, self.uid
        activity_id = self.test_pool.create_activity(
            cr, uid, {'parent_id': self.spell2_id}, {})
        self.activity_pool.write(cr, uid, activity_id,
                                 {'user_ids': [[6, 0, [self.nu_id]]]})

        # Scenario 1: Update users with empty user_ids parameter - does nothing
        self.assertTrue(self.activity_pool.update_users(cr, uid, []))

        # Scenario 2: Update user nu_id
        self.assertTrue(self.activity_pool.update_users(cr, uid, [self.nu_id]))
        self.assertFalse(self.activity_pool.read(
            cr, uid, activity_id, ['user_ids'])['user_ids'],
            msg="The activity should not have any responsible users")

        # Scenario 3: Update activity location
        self.activity_pool.write(cr, uid, activity_id,
                                 {'location_id': self.wu_id})
        self.assertTrue(self.wmu_id in self.activity_pool.read(
            cr, uid, activity_id, ['user_ids'])['user_ids'],
            msg="Responsible users not updated correctly after "
                "location assigned to the activity")

    def test_04_update_spell_users(self):
        cr, uid = self.cr, self.uid

        # Scenario 1:
        # Update spell users with empty user_ids parameter - does nothing
        self.assertTrue(self.activity_pool.update_spell_users(cr, uid))

        # Scenario 2: Update spell location
        self.activity_pool.write(cr, uid, self.spell2_id,
                                 {'location_id': self.wu_id})
        self.assertTrue(self.wmu_id in self.activity_pool.read(
            cr, uid, self.spell2_id, ['user_ids'])['user_ids'],
            msg="Responsible users not updated correctly "
                "after location assigned to the spell")

    def test_05_trigger_policy(self):
        cr, uid = self.cr, self.uid
        activity_id = self.test2_pool.create_activity(cr, uid, {
            'parent_id': self.spell2_id}, {'field1': 'TEST0',
                                           'patient_id': self.patient2_id})
        activity2_id = self.test_pool.create_activity(cr, uid, {
            'parent_id': self.spell2_id}, {'field1': 'TEST1', 'frequency': 30,
                                           'patient_id': self.patient2_id})
        activity3_id = self.test3_pool.create_activity(cr, uid, {
            'parent_id': self.spell2_id}, {'field1': 'TEST2',
                                           'patient_id': self.patient2_id})

        # Scenario 1: Trigger empty policy - does nothing
        self.assertTrue(self.test2_pool.trigger_policy(cr, uid, activity_id),
                        msg="Error triggering policy")

        # Scenario 2:
        # Trigger simple policy. No case. No context. Domains not true
        self.assertTrue(self.test_pool.trigger_policy(cr, uid, activity2_id),
                        msg="Error triggering policy")
        # According to policy, activity 1 and 2 should be cancelled
        # due to cancel_others parameter, activity 3 should still be open.
        self.assertEqual(self.activity_pool.read(
            cr, uid, activity_id, ['state'])['state'], 'cancelled')
        self.assertEqual(self.activity_pool.read(
            cr, uid, activity2_id, ['state'])['state'], 'cancelled')
        self.assertEqual(self.activity_pool.read(
            cr, uid, activity3_id, ['state'])['state'], 'new')
        # The policy should have triggered the creation of 4 new activities,
        # 1 of each data type.
        activity_ids = self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity2_id]])
        self.assertEqual(len(activity_ids), 4)
        self.assertEqual(len(self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity2_id],
                      ['data_model', '=', 'test.activity.data.model0']])), 1)
        self.assertEqual(len(self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity2_id],
                      ['data_model', '=', 'test.activity.data.model1']])), 1)
        self.assertEqual(len(self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity2_id],
                      ['data_model', '=', 'test.activity.data.model3']])), 1)
        self.assertEqual(len(self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity2_id],
                      ['data_model', '=', 'test.activity.data.model4']])), 1)
        for activity in self.activity_pool.browse(cr, uid, activity_ids):
            if activity.data_model == 'test.activity.data.model0':
                # activity should be scheduled,
                # due in 1 hour with initialized values TEST1 and frequency 30
                self.assertEqual(activity.state, 'scheduled')
                self.assertEqual(activity.data_ref.field1, 'TEST1')
                self.assertEqual(activity.data_ref.frequency, 30)
                activity_id = activity.id
            elif activity.data_model == 'test.activity.data.model1':
                # activity should be started with initialized value TEST1
                self.assertEqual(activity.state, 'started')
                self.assertEqual(activity.data_ref.field1, 'TEST1')
            elif activity.data_model == 'test.activity.data.model3':
                # activity should be scheduled,
                # due in 30 minutes with initialized value TEST1
                # and frequency 30
                self.assertEqual(activity.state, 'scheduled')
                self.assertEqual(activity.data_ref.field1, 'TEST1')
                self.assertEqual(activity.data_ref.frequency, 30)
            elif activity.data_model == 'test.activity.data.model4':
                # activity should be completed with
                # initialized value TESTCOMPLETE
                self.assertEqual(activity.state, 'completed')
                self.assertEqual(activity.data_ref.field1, 'TESTCOMPLETE')

        # Scenario 3: Using case to control what to trigger
        self.assertTrue(self.test_pool.trigger_policy(
            cr, uid, activity_id, case=1), msg="Error triggering policy")
        # The policy should have triggered
        # the creation of 1 activity of test.activity.data.model type
        activity_ids = self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity_id]])
        self.assertEqual(len(activity_ids), 1)

        # Scenario 4: Using context and location to control what to trigger
        activity_id = activity_ids[0]
        self.assertTrue(self.test_pool.trigger_policy(
            cr, uid, activity_id, location_id=self.wu_id),
            msg="Error triggering policy")
        # The policy should have triggered the creation of 2 activities
        activity_ids = self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity_id]])
        self.assertEqual(len(activity_ids), 2)
        self.assertEqual(len(self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity2_id],
                      ['data_model', '=', 'test.activity.data.model0']])), 1)
        self.assertEqual(len(self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity2_id],
                      ['data_model', '=', 'test.activity.data.model4']])), 1)
        for activity in self.activity_pool.browse(cr, uid, activity_ids):
            activity_id = activity.id if \
                activity.data_model == 'test.activity.data.model0' \
                else activity_id
        self.assertTrue(self.test_pool.trigger_policy(cr, uid, activity_id,
                                                      location_id=self.wt_id),
                        msg="Error triggering policy")
        # The policy should have triggered the creation of 1 activity
        # of test.activity.data.model type
        activity_ids = self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity_id]])
        self.assertEqual(len(activity_ids), 1)

        # Scenario 5: Using domain to control the activity trigger.
        # The second activity won't be triggered if we have
        # a completed test.activity.data.model type
        activity_id = activity_ids[0]
        self.activity_pool.complete(cr, uid, activity_id)
        self.assertTrue(self.test_pool.trigger_policy(
            cr, uid, activity_id, case=2), msg="Error triggering policy")
        # The policy should have triggered nothing
        activity_ids = self.activity_pool.search(
            cr, uid, [['creator_id', '=', activity_id]])
        self.assertEqual(len(activity_ids), 0)
