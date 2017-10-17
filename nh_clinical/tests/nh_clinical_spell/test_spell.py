# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import logging
from mock import MagicMock

from openerp.tests import common
from openerp.osv.orm import except_orm

_logger = logging.getLogger(__name__)


class TestClinicalSpell(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestClinicalSpell, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.patient_pool = cls.registry('nh.clinical.patient')
        cls.spell_pool = cls.registry('nh.clinical.spell')
        cls.activity_pool = cls.registry('nh.activity')
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.group_pool = cls.registry('res.groups')
        cls.user_pool = cls.registry('res.users')
        cls.api_pool = cls.registry('nh.clinical.api')

        cls.hospital_id = cls.location_pool.create(
            cr, uid, {'name': 'Test Hospital', 'code': 'TESTHOSP',
                      'usage': 'hospital'})
        cls.pos_id = cls.pos_pool.create(
            cr, uid, {'name': 'Test POS', 'location_id': cls.hospital_id})
        group_ids = cls.group_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Admin Group']])
        cls.userpos_id = cls.user_pool.create(
            cr, uid, {'name': 'Test User', 'login': 'user_001',
                      'password': 'user_001', 'groups_id': [[4, group_ids[0]]],
                      'pos_id': cls.pos_id})
        cls.ward_id = cls.location_pool.create(
            cr, uid, {'name': 'Test Ward', 'code': 'TESTWARD', 'usage': 'ward',
                      'parent_id': cls.hospital_id, 'type': 'poc'})
        cls.patient_id = cls.patient_pool.create(
            cr, uid, {'other_identifier': 'TESTHN01'})
        cls.patient2_id = cls.patient_pool.create(
            cr, uid, {'other_identifier': 'TESTHN02'})

        cls.spell_id_1 = 1

        cls.spell_id_2 = 2
        cls.spell_ids = [cls.spell_id_1, cls.spell_id_2]
        cls.return_value = [
            {'activity_id': 1, 'spell_id': cls.spell_id_1,
             'user_ids': (3, 4, 5)},
            {'activity_id': 2, 'spell_id': cls.spell_id_2,
             'user_ids': (2, 2, 5)}
        ]

    def test_01_get_by_patient_id(self):
        cr, uid = self.cr, self.uid

        activity_id = self.spell_pool.create_activity(cr, uid, {}, {
            'patient_id': self.patient_id,
            'location_id': self.ward_id,
            'pos_id': self.pos_id,
            'code': 'TESTSPELL001',
            'start_date': '2000-01-01 00:00:00'
        })
        self.activity_pool.start(cr, uid, activity_id)
        activity = self.activity_pool.browse(cr, uid, activity_id)

        # Scenario 1: Spell exists
        self.assertEqual(self.spell_pool.get_by_patient_id(
            cr, uid, self.patient_id), activity.data_ref.id)

        # Scenario 2: Spell does not exist
        self.assertFalse(self.spell_pool.get_by_patient_id(cr, uid,
                                                           self.patient2_id))

        # Scenario 3: Exception 'True', Spell exists
        with self.assertRaises(except_orm):
            self.spell_pool.get_by_patient_id(cr, uid, self.patient_id,
                                              exception='True')

        # Scenario 4: Exception 'False', Spell does not exist
        with self.assertRaises(except_orm):
            self.spell_pool.get_by_patient_id(cr, uid, self.patient2_id,
                                              exception='False')

    def test_02_get_transferred_user_ids(self):
        cr, uid = self.cr, self.uid
        cr.dictfetchall = MagicMock(return_value=self.return_value)

        result = self.spell_pool._get_transferred_user_ids(
            cr, uid, self.spell_ids, 'transferred_user_ids', None)
        self.assertEquals(result, {1: [3, 4, 5], 2: [2, 5]})
        del cr.dictfetchall

    def test_03_transferred_user_ids_search_with_multiple_user_ids(self):
        cr, uid = self.cr, self.uid
        args = [('user_id', 'in', [3, 4, 5])]
        return_value = {1: [3, 4, 5], 2: [2, 5], 3: [6, 7]}
        self.spell_pool._get_transferred_user_ids = MagicMock(
            return_value=return_value)

        result = self.spell_pool._transferred_user_ids_search(cr, uid, None,
                                                              None, args)
        self.assertEquals([('id', 'in', [1, 2])], result)
        del self.spell_pool._get_transferred_user_ids

    def test_04_test_create_when_patients_is_started_spell(self):
        cr, uid = self.cr, self.uid
        values = {'patient_id': 2}
        self.spell_pool.search = MagicMock(return_value=[1])

        result = self.spell_pool.create(cr, uid, values)
        self.assertEquals(1, result)
        del self.spell_pool.search

    def test_05_test_get_activity_user_ids_when_no_activity_id(self):
        cr, uid = self.cr, self.uid
        cr.fetchone = MagicMock(return_value=(None,))

        result = self.spell_pool.get_activity_user_ids(cr, uid, 2)
        self.assertEquals(result, [])
        del cr.fetchone

    def test_06_test_get_activity_user_ids_when_activity_id_and_user_ids(self):
        cr, uid = self.cr, self.uid
        cr.fetchone = MagicMock(return_value=(1, 2))
        cr.dictfetchone = MagicMock(
            return_value={'activity_id': 1, 'user_ids': [2, 3, 4]})

        result = self.spell_pool.get_activity_user_ids(cr, uid, 2)
        self.assertEquals(result, [2, 3, 4])
        del cr.fetchone, cr.dictfetchone

    def test_07_test_get_activity_user_ids_when_no_user_ids(self):
        cr, uid = self.cr, self.uid
        cr.fetchone = MagicMock(return_value=(1, 2))
        cr.dictfetchone = MagicMock(
            return_value={'activity_id': 1, 'user_ids': []})

        result = self.spell_pool.get_activity_user_ids(cr, uid, 2)
        self.assertEquals(result, [])
        del cr.fetchone, cr.dictfetchone
