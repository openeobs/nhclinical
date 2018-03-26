# -*- coding: utf-8 -*-
# Part of NHClinical. See LICENSE file for full copyright and licensing details
from datetime import datetime as dt

from faker import Faker
from openerp.osv.orm import except_orm
from openerp.tests import common
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf

fake = Faker()


class TestAuditing(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestAuditing, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.users_pool = cls.registry('res.users')
        cls.groups_pool = cls.registry('res.groups')
        cls.activity_pool = cls.registry('nh.activity')
        cls.patient_pool = cls.registry('nh.clinical.patient')
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.spell_pool = cls.registry('nh.clinical.spell')
        cls.activate_pool = cls.registry('nh.clinical.location.activate')
        cls.deactivate_pool = cls.registry('nh.clinical.location.deactivate')
        cls.move_pool = cls.registry('nh.clinical.patient.move')

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
        cls.adt_id = cls.users_pool.search(
            cr, uid, [('groups_id.name', 'in', ['NH Clinical ADT Group']),
                      ('pos_id', '=', cls.pos_id)])[0]

    def test_location_activate(self):
        """
        Tests Location Activate activity
        """
        cr, uid = self.cr, self.uid

        # Scenario 1: Activating an inactive location
        active_location_id = self.location_pool.search(cr, uid, [
            ['parent_id', '=', self.wu_id],
            ['active', '=', True],
            ['is_available', '=', True]])
        self.assertTrue(active_location_id,
                        msg="Pre-state for Activate Location: "
                            "No location found!")
        deactivate_location = self.location_pool.write(
            cr, uid, active_location_id[0], {'active': False})
        self.assertTrue(deactivate_location,
                        msg="Pre-state for Activate Location: "
                            "Deactivating location failed")
        activity_id = self.activate_pool.create_activity(
            cr, uid, {}, {'location_id': active_location_id[0]})
        self.assertTrue(activity_id, msg="Activate Location creation failed")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(
            activity.data_ref.location_id.id, active_location_id[0],
            msg="Activate Location data location not stored properly")
        self.activity_pool.complete(cr, uid, activity_id)
        location = self.location_pool.browse(cr, uid, active_location_id[0])
        self.assertTrue(location.active,
                        msg="Activate Location completion failed")

        # Scenario 2: Activating an active location
        activity_id = self.activate_pool.create_activity(
            cr, uid, {}, {'location_id': active_location_id[0]})
        self.activity_pool.complete(cr, uid, activity_id)
        location = self.location_pool.browse(cr, uid, active_location_id[0])
        self.assertTrue(location.active,
                        msg="Scenario 2 Activate Location completion failed")

        # Scenario 3: Trying to complete Activate Location without Location
        activity_id = self.activate_pool.create_activity(cr, uid, {}, {})
        with self.assertRaises(except_orm):
            self.activity_pool.complete(cr, uid, activity_id)

    def test_location_deactivate(self):
        """
        Tests Location Deactivate activity
        """
        cr, uid = self.cr, self.uid

        # Scenario 1: Deactivating an active location
        active_location_id = self.location_pool.search(cr, uid, [
            ['parent_id', '=', self.wu_id],
            ['active', '=', True],
            ['is_available', '=', True]])
        self.assertTrue(active_location_id,
                        msg="Pre-state for Deactivate Location: "
                            "No location found!")
        activity_id = self.deactivate_pool.create_activity(
            cr, uid, {}, {'location_id': active_location_id[0]})
        self.assertTrue(activity_id, msg="Deactivate Location creation failed")
        activity = self.activity_pool.browse(cr, uid, activity_id)
        self.assertEqual(
            activity.data_ref.location_id.id, active_location_id[0],
            msg="Deactivate Location data location not stored properly")
        self.activity_pool.complete(cr, uid, activity_id)
        location = self.location_pool.browse(cr, uid, active_location_id[0])
        self.assertFalse(location.active,
                         msg="Deactivate Location completion failed")

        # Scenario 2: Deactivating an inactive location
        activity_id = self.deactivate_pool.create_activity(
            cr, uid, {}, {'location_id': active_location_id[0]})
        self.activity_pool.complete(cr, uid, activity_id)
        location = self.location_pool.browse(cr, uid, active_location_id[0])
        self.assertFalse(
            location.active,
            msg="Scenario 2 Deactivate Location completion failed")

        # Scenario 3: Trying to complete Deactivate Location without Location
        activity_id = self.deactivate_pool.create_activity(cr, uid, {}, {})
        with self.assertRaises(except_orm):
            self.activity_pool.complete(cr, uid, activity_id)

        # Scenario 4: Deactivating a location that is being used by a patient
        patient_id = fake.random_element(self.patient_ids)
        spell_id = self.spell_pool.create_activity(cr, uid, {}, {
            'patient_id': patient_id,
            'location_id': active_location_id[1],
            'pos_id': self.pos_id,
            'code': 'TESTSPELL0001',
            'start_date': dt.now().strftime(dtf)})
        self.activity_pool.start(cr, uid, spell_id)
        location = self.location_pool.browse(cr, uid, active_location_id[1])
        self.assertFalse(location.is_available,
                         msg="Scenario 4 Pre-state: Location is available")
        activity_id = self.deactivate_pool.create_activity(
            cr, uid, {}, {'location_id': active_location_id[1]})
        with self.assertRaises(except_orm):
            self.activity_pool.complete(cr, uid, activity_id)

    def test_location_activation_auditing(self):
        """
        Tests that Location Activate/Deactivate is being audited
        """
        cr, uid = self.cr, self.uid

        # Scenario 1: Deactivating an active location
        active_location_id = self.location_pool.search(cr, uid, [
            ['parent_id', '=', self.wt_id],
            ['active', '=', True],
            ['is_available', '=', True]])
        self.assertTrue(active_location_id,
                        msg="Pre-state for Activate/Deactivate "
                            "Location Auditing: No location found!")
        self.location_pool.switch_active_status(cr, self.wmt_id,
                                                active_location_id)
        audit_activity_id = self.activity_pool.search(cr, uid, [
            ['location_id', '=', active_location_id[0]],
            ['state', '=', 'completed'],
            ['data_model', '=', 'nh.clinical.location.deactivate']
        ])
        self.assertTrue(audit_activity_id,
                        msg="Audit activity not found "
                            "after deactivating the Location")
        audit_activity = self.activity_pool.browse(cr, uid,
                                                   audit_activity_id[0])
        self.assertEqual(audit_activity.terminate_uid.id, self.wmt_id,
                         msg="Audit activity: Wrong user recorded")

        # Scenario 2: Activating an inactive location
        self.location_pool.switch_active_status(cr, self.wmt_id,
                                                active_location_id)
        audit_activity_id = self.activity_pool.search(cr, uid, [
            ['location_id', '=', active_location_id[0]],
            ['state', '=', 'completed'],
            ['data_model', '=', 'nh.clinical.location.activate']
        ])
        self.assertTrue(audit_activity_id,
                        msg="Audit activity not found "
                            "after activating the Location")
        audit_activity = self.activity_pool.browse(cr, uid,
                                                   audit_activity_id[0])
        self.assertEqual(audit_activity.terminate_uid.id, self.wmt_id,
                         msg="Audit activity: Wrong user recorded")
