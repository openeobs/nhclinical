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
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.spell_pool = cls.registry('nh.clinical.spell')
        cls.test_pool = cls.registry('test.activity.data.model')

        cls.apidemo = cls.registry('nh.clinical.api.demo')

        cls.patient_ids = cls.apidemo.build_unit_test_env1(cr, uid, bed_count=4, patient_count=4)

        cls.wu_id = cls.location_pool.search(cr, uid, [('code', '=', 'U')])[0]
        cls.wt_id = cls.location_pool.search(cr, uid, [('code', '=', 'T')])[0]
        cls.pos_id = cls.location_pool.read(cr, uid, cls.wu_id, ['pos_id'])['pos_id'][0]
        cls.pos_location_id = cls.pos_pool.read(cr, uid, cls.pos_id, ['location_id'])['location_id'][0]

        cls.wmu_id = cls.users_pool.search(cr, uid, [('login', '=', 'WMU')])[0]
        cls.wmt_id = cls.users_pool.search(cr, uid, [('login', '=', 'WMT')])[0]
        cls.nu_id = cls.users_pool.search(cr, uid, [('login', '=', 'NU')])[0]
        cls.nt_id = cls.users_pool.search(cr, uid, [('login', '=', 'NT')])[0]
        cls.adt_id = cls.users_pool.search(cr, uid, [('groups_id.name', 'in', ['NH Clinical ADT Group']), ('pos_id', '=', cls.pos_id)])[0]

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
        spell_activity_id = cls.spell_pool.create_activity(cr, uid, {}, spell_data)
        cls.activity_pool.start(cr, uid, spell_activity_id)
        cls.spell_id = spell_activity_id
        spell_activity_id = cls.spell_pool.create_activity(cr, uid, {}, spell2_data)
        cls.activity_pool.start(cr, uid, spell_activity_id)
        cls.spell2_id = spell_activity_id
        cls.patient_id = patient_id
        cls.patient2_id = patient2_id

    def test_01_audit_ward_manager(self):
        cr, uid = self.cr, self.uid

        self.assertFalse(self.spell_pool._audit_ward_manager(cr, uid, self.spell_id), msg="Audit Ward Manager should return False when the activity has no location")
        # try to write without data
        self.assertTrue(self.activity_pool.write(cr, uid, self.spell_id, False), msg="Error on activity write")
        # include location_id in data
        self.assertTrue(self.activity_pool.write(cr, uid, self.spell_id, {'location_id': self.wu_id}))
        self.assertTrue(self.spell_pool._audit_ward_manager(cr, uid, [self.spell_id]), msg="Audit Ward Manager failed")
        spell = self.activity_pool.browse(cr, uid, self.spell_id)
        self.assertEqual(spell.ward_manager_id.id, self.wmu_id, msg="Audit Ward Manager recorded the wrong user id")
        self.activity_pool.write(cr, uid, self.spell_id, {'location_id': self.wt_id})
        self.activity_pool.complete(cr, uid, self.spell_id)
        spell = self.activity_pool.browse(cr, uid, self.spell_id)
        self.assertEqual(spell.ward_manager_id.id, self.wmt_id, msg="Audit Ward Manager failed or recorded the wrong user id on Complete")

    def test_02_cancel_open_activities(self):
        cr, uid = self.cr, self.uid

        activity_id = self.test_pool.create_activity(cr, uid, {'parent_id': self.spell2_id}, {})
        self.assertTrue(self.activity_pool.cancel_open_activities(cr, uid, self.spell2_id, 'test.activity.data.model'))
        self.assertEqual(self.activity_pool.read(cr, uid, activity_id, ['state'])['state'], 'cancelled')

    def test_03_update_users(self):
        cr, uid = self.cr, self.uid
        activity_id = self.test_pool.create_activity(cr, uid, {'parent_id': self.spell2_id}, {})
        self.activity_pool.write(cr, uid, activity_id, {'user_ids': [[6, 0, [self.nu_id]]]})

        # Scenario 1: Update users with empty user_ids parameter - does nothing
        self.assertTrue(self.activity_pool.update_users(cr, uid))

        # Scenario 2: Update user nu_id
        self.assertTrue(self.activity_pool.update_users(cr, uid, [self.nu_id]))
        self.assertFalse(self.activity_pool.read(cr, uid, activity_id, ['user_ids'])['user_ids'],
                         msg="The activity should not have any responsible users")

        # Scenario 3: Update activity location
        self.activity_pool.write(cr, uid, activity_id, {'location_id': self.wu_id})
        self.assertTrue(self.wmu_id in self.activity_pool.read(cr, uid, activity_id, ['user_ids'])['user_ids'],
                        msg="Responsible users not updated correctly after location assigned to the activity")

    def test_04_update_spell_users(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Update spell users with empty user_ids parameter - does nothing
        self.assertTrue(self.activity_pool.update_spell_users(cr, uid))

        # Scenario 2: Update spell location
        self.activity_pool.write(cr, uid, self.spell2_id, {'location_id': self.wu_id})
        self.assertTrue(self.wmu_id in self.activity_pool.read(cr, uid, self.spell2_id, ['user_ids'])['user_ids'],
                        msg="Responsible users not updated correctly after location assigned to the spell")