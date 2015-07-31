import logging

from openerp.tests.common import SingleTransactionCase
from openerp.osv.orm import except_orm

_logger = logging.getLogger(__name__)


class TestUsers(SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestUsers, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.user_pool = cls.registry('res.users')
        cls.groups_pool = cls.registry('res.groups')
        cls.partner_pool = cls.registry('res.partner')
        cls.title_pool = cls.registry('res.partner.title')
        cls.activity_pool = cls.registry('nh.activity')
        cls.patient_pool = cls.registry('nh.clinical.patient')
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.spell_pool = cls.registry('nh.clinical.spell')
        cls.doctor_pool = cls.registry('nh.clinical.doctor')

        cls.admin_group_id = cls.groups_pool.search(cr, uid, [['name', '=', 'NH Clinical Admin Group']])
        cls.dr_group_id = cls.groups_pool.search(cr, uid, [['name', '=', 'NH Clinical Doctor Group']])[0]

        cls.hospital_id = cls.location_pool.create(cr, uid, {'name': 'Test Hospital', 'code': 'TESTHOSP',
                                                             'usage': 'hospital'})
        cls.pos_id = cls.pos_pool.create(cr, uid, {'name': 'Test POS', 'location_id': cls.hospital_id})

        cls.adt_uid = cls.user_pool.create(cr, uid, {'name': 'Admin 0', 'login': 'user_000',
                                                        'password': 'user_000',
                                                        'groups_id': [[4, cls.admin_group_id[0]]],
                                                        'pos_id': cls.pos_id})

        cls.admin_uid = cls.user_pool.create(cr, uid, {'name': 'Admin 1', 'login': 'user_001',
                                                        'password': 'user_001',
                                                        'groups_id': [[4, cls.admin_group_id[0]]]})

        cls.doctor_id = cls.doctor_pool.create(cr, uid, {'name': 'Doctor01', 'gender': 'M', 'code': 'DOCT01'})
        cls.dr_title_id = cls.title_pool.create(cr, uid, {'name': 'Dr'})

    def test_01_check_pos(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Check PoS without exception

        self.assertTrue(self.user_pool.check_pos(cr, uid, self.adt_uid))
        self.assertFalse(self.user_pool.check_pos(cr, uid, self.admin_uid))

        # Scenario 2: Check PoS with exception parameter

        self.assertTrue(self.user_pool.check_pos(cr, uid, self.adt_uid, exception=True))
        with self.assertRaises(except_orm):
            self.user_pool.check_pos(cr, uid, self.admin_uid, exception=True)

    def test_02_create(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Create a new user linked to a doctor object
        user_id = self.user_pool.create(cr, uid, {
            'name': 'Dr1', 'login': 'dr1', 'password': 'dr1', 'doctor_id': self.doctor_id,
            'groups_id': [[4, self.dr_group_id]], 'title': self.dr_title_id})
        doctor = self.doctor_pool.browse(cr, uid, self.doctor_id)
        self.assertEqual(doctor.user_id.id, user_id)
        user = self.user_pool.browse(cr, uid, user_id)
        self.assertTrue(user.partner_id.doctor)

    def test_03_name_get(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Get name for a normal user
        name = self.user_pool.name_get(cr, uid, self.admin_uid, context=None)
        self.assertEqual(name[0][1], 'Admin 1')

        # Scenario 2: Get name for a doctor user
        doctor_uid = self.user_pool.search(cr, uid, [['name', '=', 'Dr1']])[0]
        name = self.user_pool.name_get(cr, uid, doctor_uid)
        self.assertEqual(name[0][1], 'Dr Dr1')

        # Scenario 3: Get name for a user with related company
        company_id = self.partner_pool.create(cr, uid, {'name': 'Company1'})
        self.user_pool.write(cr, uid, self.admin_uid, {'parent_id': company_id, 'city': 'City1', 'email': 'a@b.org'})
        name = self.user_pool.name_get(cr, uid, self.admin_uid)
        self.assertEqual(name[0][1], 'Company1, Admin 1')

        # Scenario 4: Get only address
        name = self.user_pool.name_get(cr, uid, self.admin_uid, {'show_address_only': 1})
        self.assertEqual(name[0][1], '\nCity1  \n')

        # Scenario 5: Get name and address
        name = self.user_pool.name_get(cr, uid, self.admin_uid, {'show_address': 1})
        self.assertEqual(name[0][1], "Company1, Admin 1\nCity1  \n")

        # Scenario 6: Get name and email
        name = self.user_pool.name_get(cr, uid, self.admin_uid, {'show_email': 1})
        self.assertEqual(name[0][1], "Company1, Admin 1 <a@b.org>")