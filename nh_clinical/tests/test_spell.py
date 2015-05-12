import logging

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

        cls.hospital_id = cls.location_pool.create(cr, uid, {'name': 'Test Hospital', 'code': 'TESTHOSP',
                                                             'usage': 'hospital'})
        cls.pos_id = cls.pos_pool.create(cr, uid, {'name': 'Test POS', 'location_id': cls.hospital_id})
        group_ids = cls.group_pool.search(cr, uid, [['name', '=', 'NH Clinical Admin Group']])
        cls.userpos_id = cls.user_pool.create(cr, uid, {'name': 'Test User', 'login': 'user_001',
                                                        'password': 'user_001', 'groups_id': [[4, group_ids[0]]],
                                                        'pos_id': cls.pos_id})
        cls.ward_id = cls.location_pool.create(cr, uid, {'name': 'Test Ward', 'code': 'TESTWARD', 'usage': 'ward',
                                                         'parent_id': cls.hospital_id, 'type': 'poc'})
        cls.patient_id = cls.patient_pool.create(cr, uid, {'other_identifier': 'TESTHN01'})
        cls.patient2_id = cls.patient_pool.create(cr, uid, {'other_identifier': 'TESTHN02'})

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
        self.assertEqual(self.spell_pool.get_by_patient_id(cr, uid, self.patient_id), activity.data_ref.id)

        # Scenario 2: Spell does not exist
        self.assertFalse(self.spell_pool.get_by_patient_id(cr, uid, self.patient2_id))

        # Scenario 3: Exception 'True', Spell exists
        with self.assertRaises(except_orm):
            self.spell_pool.get_by_patient_id(cr, uid, self.patient_id, exception='True')

        # Scenario 4: Exception 'False', Spell does not exist
        with self.assertRaises(except_orm):
            self.spell_pool.get_by_patient_id(cr, uid, self.patient2_id, exception='False')