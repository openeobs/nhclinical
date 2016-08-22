# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
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
        cls.category_pool = cls.registry('res.partner.category')
        cls.activity_pool = cls.registry('nh.activity')
        cls.patient_pool = cls.registry('nh.clinical.patient')
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.spell_pool = cls.registry('nh.clinical.spell')
        cls.doctor_pool = cls.registry('nh.clinical.doctor')
        cls.mail_pool = cls.registry('mail.message')
        cls.config_pool = cls.registry('ir.config_parameter')

        cls.admin_group_id = cls.groups_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Admin Group']])
        cls.dr_group_id = cls.groups_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Doctor Group']])[0]
        cls.wm_group_id = cls.groups_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Shift Coordinator Group']])[0]
        cls.nurse_group_id = cls.groups_pool.search(
            cr, uid, [['name', '=', 'NH Clinical Nurse Group']])[0]
        cls.hca_group_id = cls.groups_pool.search(
            cr, uid, [['name', '=', 'NH Clinical HCA Group']])[0]
        cls.employee_group_id = cls.groups_pool.search(
            cr, uid, [['name', '=', 'Employee']])[0]
        cls.cc_group_id = cls.groups_pool.search(
            cr, uid, [['name', '=', 'Contact Creation']])[0]

        cls.admin_role_id = cls.category_pool.search(
            cr, uid, [['name', '=', 'System Administrator']])[0]
        cls.wm_role_id = cls.category_pool.search(
            cr, uid, [['name', '=', 'Shift Coordinator']])[0]
        cls.nurse_role_id = cls.category_pool.search(
            cr, uid, [['name', '=', 'Nurse']])[0]
        cls.hca_role_id = cls.category_pool.search(cr, uid,
                                                   [['name', '=', 'HCA']])[0]

        cls.hospital_id = cls.location_pool.create(
            cr, uid, {'name': 'Test Hospital', 'code': 'TESTHOSP',
                      'usage': 'hospital'})
        cls.pos_id = cls.pos_pool.create(
            cr, uid, {'name': 'Test POS', 'location_id': cls.hospital_id})

        cls.adt_uid = cls.user_pool.create(
            cr, uid, {'name': 'Admin 0', 'login': 'user_000',
                      'password': 'user_000',
                      'groups_id': [[4, cls.admin_group_id[0]]],
                      'category_id': [[4, cls.admin_role_id]],
                      'pos_ids': [[6, 0, [cls.pos_id]]]})

        cls.admin_uid = cls.user_pool.create(
            cr, uid, {'name': 'Admin 1', 'login': 'user_001',
                      'password': 'user_001',
                      'groups_id': [[4, cls.admin_group_id[0]]]})
        cls.wm_uid = cls.user_pool.search(
            cr, uid, [['name', '=', 'WM0 Test']]
        )[0]

        cls.doctor_id = cls.doctor_pool.create(
            cr, uid, {'name': 'Doctor01', 'gender': 'M', 'code': 'DOCT01'})
        cls.dr_title_id = cls.title_pool.create(cr, uid, {'name': 'Dr'})

    def test_01_check_pos(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Check PoS without exception

        self.assertTrue(self.user_pool.check_pos(cr, uid, self.adt_uid))
        self.assertFalse(self.user_pool.check_pos(cr, uid, self.admin_uid))

        # Scenario 2: Check PoS with exception parameter

        self.assertTrue(self.user_pool.check_pos(cr, uid, self.adt_uid,
                                                 exception=True))
        with self.assertRaises(except_orm):
            self.user_pool.check_pos(cr, uid, self.admin_uid, exception=True)

    def test_02_update_group_vals(self):
        cr, uid = self.cr, self.uid

        vals = {
            'groups_id': [[4, self.admin_group_id[0]]]
        }
        check_vals = vals.copy()

        # Scenario 1: Update values without updating category_id field
        self.assertTrue(self.user_pool.update_group_vals(cr, uid, False, vals))
        self.assertDictEqual(vals, check_vals)

        # Scenario 2:
        # Update values with incorrect formatted category_id field values.
        vals['category_id'] = 7
        with self.assertRaises(except_orm):
            self.user_pool.update_group_vals(cr, uid, False, vals)
        vals['category_id'] = [7]
        with self.assertRaises(except_orm):
            self.user_pool.update_group_vals(cr, uid, False, vals)
        vals['category_id'] = [[7]]
        with self.assertRaises(except_orm):
            self.user_pool.update_group_vals(cr, uid, False, vals)

        # Scenario 3.1: Add a category with groups_id having values
        vals = {
            'groups_id': [(4, self.admin_group_id[0])],
            'category_id': [(4, self.wm_role_id)]
        }
        self.assertTrue(self.user_pool.update_group_vals(cr, uid, False, vals))
        self.assertIn((4, self.wm_group_id), vals['groups_id'])
        self.assertIn((4, self.cc_group_id), vals['groups_id'])
        self.assertIn((4, self.admin_group_id[0]), vals['groups_id'])

        # Scenario 3.2: Add a category with groups_id not having values
        vals = {'category_id': [(4, self.wm_role_id)]}
        self.assertTrue(self.user_pool.update_group_vals(cr, uid, False, vals))
        self.assertIn((4, self.wm_group_id), vals.get('groups_id'))
        self.assertIn((4, self.cc_group_id), vals['groups_id'])
        self.assertNotIn((4, self.admin_group_id[0]), vals['groups_id'])

        # Scenario 4.1: Remove a category with no user_id provided
        vals = {
            'category_id': [(3, self.wm_role_id)]
        }
        self.assertTrue(self.user_pool.update_group_vals(cr, uid, False, vals))
        self.assertIn((3, self.wm_group_id), vals['groups_id'])
        self.assertIn((3, self.cc_group_id), vals['groups_id'])
        self.assertNotIn((3, self.employee_group_id), vals['groups_id'])

        # Scenario 4.2: Remove all categories no user_id provided
        vals = {'category_id': [[5]]}
        self.assertTrue(self.user_pool.update_group_vals(cr, uid, False, vals))
        self.assertIn((3, self.wm_group_id), vals['groups_id'])
        self.assertIn((3, self.hca_group_id), vals['groups_id'])
        self.assertIn((3, self.nurse_group_id), vals['groups_id'])
        self.assertIn((3, self.dr_group_id), vals['groups_id'])
        self.assertIn((3, self.cc_group_id), vals['groups_id'])
        self.assertNotIn((3, self.employee_group_id), vals['groups_id'])

        # Scenario 4.3: Remove a category with user_id provided
        vals = {
            'category_id': [(3, self.wm_role_id)]
        }
        self.assertTrue(self.user_pool.update_group_vals(cr, uid, self.adt_uid,
                                                         vals))
        self.assertIn((3, self.wm_group_id), vals['groups_id'])
        self.assertNotIn((3, self.cc_group_id), vals['groups_id'])
        self.assertNotIn((3, self.employee_group_id), vals['groups_id'])

        # Scenario 4.4: Add and remove a category
        vals = {
            'category_id': [(3, self.wm_role_id), (4, self.admin_role_id)]
        }
        self.assertTrue(self.user_pool.update_group_vals(cr, uid, False, vals))
        self.assertIn((3, self.wm_group_id), vals['groups_id'])
        self.assertIn((4, self.admin_group_id[0]), vals['groups_id'])
        self.assertIn((4, self.cc_group_id), vals['groups_id'])
        self.assertNotIn((3, self.cc_group_id), vals['groups_id'])
        self.assertNotIn((3, self.employee_group_id), vals['groups_id'])

        # Scenario 5.1: Replace categories with user_id provided
        vals = {
            'category_id': [[6, 0, [self.wm_role_id]]]
        }
        self.assertTrue(self.user_pool.update_group_vals(cr, uid, self.adt_uid,
                                                         vals))
        self.assertIn((3, self.admin_group_id[0]), vals['groups_id'])
        self.assertIn((4, self.wm_group_id), vals['groups_id'])
        self.assertNotIn((4, self.cc_group_id), vals['groups_id'])
        self.assertNotIn((3, self.cc_group_id), vals['groups_id'])
        self.assertNotIn((3, self.employee_group_id), vals['groups_id'])

        # Scenario 5.2: Replace categories with no user_id provided
        vals = {'category_id': [[6, 0, [self.wm_role_id]]]}
        self.assertTrue(self.user_pool.update_group_vals(cr, uid, False, vals))
        self.assertNotIn((3, self.admin_group_id[0]), vals['groups_id'])
        self.assertIn((4, self.wm_group_id), vals['groups_id'])
        self.assertIn((4, self.cc_group_id), vals['groups_id'])
        self.assertNotIn((3, self.cc_group_id), vals['groups_id'])
        self.assertNotIn((3, self.employee_group_id), vals['groups_id'])

    def test_03_create(self):
        cr, uid = self.cr, self.uid

        # Scenario 1: Create a new user linked to a doctor object
        user_id = self.user_pool.create(
            cr, uid, {'name': 'Dr1', 'login': 'dr1', 'password': 'dr1',
                      'doctor_id': self.doctor_id,
                      'groups_id': [[4, self.dr_group_id]],
                      'title': self.dr_title_id})
        doctor = self.doctor_pool.browse(cr, uid, self.doctor_id)
        self.assertEqual(doctor.user_id.id, user_id)
        user = self.user_pool.browse(cr, uid, user_id)
        self.assertTrue(user.partner_id.doctor)

    def test_04_name_get(self):
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
        self.user_pool.write(
            cr, uid, self.admin_uid,
            {'parent_id': company_id, 'city': 'City1', 'email': 'a@b.org'})
        name = self.user_pool.name_get(cr, uid, self.admin_uid)
        self.assertEqual(name[0][1], 'Company1, Admin 1')

        # Scenario 4: Get only address
        name = self.user_pool.name_get(cr, uid, self.admin_uid,
                                       {'show_address_only': 1})
        self.assertEqual(name[0][1], '\nCity1  \n')

        # Scenario 5: Get name and address
        name = self.user_pool.name_get(cr, uid, self.admin_uid,
                                       {'show_address': 1})
        self.assertEqual(name[0][1], "Company1, Admin 1\nCity1  \n")

        # Scenario 6: Get name and email
        name = self.user_pool.name_get(cr, uid, self.admin_uid,
                                       {'show_email': 1})
        self.assertEqual(name[0][1], "Company1, Admin 1 <a@b.org>")

    def test_05_mail_message_get_default_from(self):
        cr, uid = self.cr, self.uid

        user_uid = self.user_pool.create(
            cr, uid, {'name': 'Admin 2', 'login': 'user_002',
                      'password': 'user_002',
                      'groups_id': [[4, self.admin_group_id[0]]]})

        # Scenario 1: No mail
        self.assertEqual(self.mail_pool._get_default_from(cr, user_uid),
                         'Admin 2 <No email>')

        # Scenario 2: Email
        self.user_pool.write(cr, uid, user_uid, {'email': 'a@b.org'})
        self.assertEqual(self.mail_pool._get_default_from(cr, user_uid),
                         'Admin 2 <a@b.org>')

        # Scenario 3: Alias name and domain
        self.user_pool.write(cr, uid, user_uid, {'alias_name': 'c'})
        self.config_pool.set_param(cr, uid, 'mail.catchall.domain', 'd.com')
        self.assertEqual(self.mail_pool._get_default_from(cr, user_uid),
                         'Admin 2 <c@d.com>')

    def test_06_update_doctor_status(self):
        cr, uid = self.cr, self.uid

        dr_uid = self.user_pool.create(
            cr, uid, {'name': 'Dr 3', 'login': 'user_003',
                      'password': 'user_003',
                      'groups_id': [[4, self.dr_group_id]]})
        user_uid = self.user_pool.create(
            cr, uid, {'name': 'U04', 'login': 'user_004',
                      'password': 'user_004', 'doctor': True})

        self.assertTrue(self.user_pool.update_doctor_status(
            cr, uid, [dr_uid, user_uid]))

    def test_07_get_groups_string(self):
        cr = self.cr
        admin = self.user_pool.get_groups_string(cr, self.adt_uid)
        shift_coordinator = self.user_pool.get_groups_string(cr, self.wm_uid)
        self.assertListEqual(admin, ['Admin'])
        self.assertListEqual(shift_coordinator, ['Shift Coordinator'])

    def test_08_create_without_pos_ids_value_automatically_adds_pos_ids(self):
        """
        Tests new user created by a user related to pos_ids, automatically
        adds the created user to those pos_ids.
        """
        cr, uid = self.cr, self.uid

        user_id = self.user_pool.create(
            cr, self.adt_uid, {'name': 'U1', 'login': 'U1', 'password': 'U1'})
        user = self.user_pool.browse(cr, uid, user_id)
        self.assertListEqual([self.pos_id], [p.id for p in user.pos_ids])

    def test_09_create_with_pos_ids_value_doesnt_add_pos_from_creator(self):
        """
        Tests new user created by a user related to pos_ids, does not
        automatically add the created user to those pos_ids if a pos_ids
        value is provided on creation.
        """
        cr, uid = self.cr, self.uid

        pos_id = self.pos_pool.create(
            cr, uid, {'name': 'POS', 'location_id': self.hospital_id})
        user_id = self.user_pool.create(
            cr, self.adt_uid,
            {'name': 'U2', 'login': 'U2', 'password': 'U2',
             'pos_ids': [[6, 0, [pos_id]]]})
        user = self.user_pool.browse(cr, uid, user_id)
        self.assertListEqual([pos_id], [p.id for p in user.pos_ids])
