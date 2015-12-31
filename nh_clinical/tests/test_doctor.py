# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import logging

from openerp.tests import common

_logger = logging.getLogger(__name__)


class TestClinicalDoctor(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestClinicalDoctor, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.doctor_pool = cls.registry('nh.clinical.doctor')
        cls.partner_pool = cls.registry('res.partner')
        cls.user_pool = cls.registry('res.users')

        cls.doctors = [cls.doctor_pool.create(
            cr, uid, {'name': 'doct'+str(i), 'code': '000'}) for i in range(2)]

    def test_01_evaluate_doctors_dict(self):
        cr, uid = self.cr, self.uid

        doctors = """[{
            'type': 'c',
            'code': 'CON01',
            'title': 'Dr.',
            'given_name': 'Consulting',
            'family_name': 'Doctor',
            'gender': 'F'
        }, {
            'type': 'r',
            'code': 'REF01',
            'given_name': 'Referring',
            'family_name': 'Doctor',
            'gender': 'M'
        }]"""

        data = {'doctors': doctors}

        # Scenario 1: Evaluate doctors and create them
        self.assertTrue(self.doctor_pool.evaluate_doctors_dict(cr, uid, data))
        con_id = self.doctor_pool.search(cr, uid, [['code', '=', 'CON01']])
        self.assertTrue(con_id, msg="Consulting Doctor not created")
        ref_id = self.doctor_pool.search(cr, uid, [['code', '=', 'REF01']])
        self.assertTrue(ref_id, msg="Referring Doctor not created")
        self.assertEqual([[6, False, con_id]], data.get('con_doctor_ids'))
        self.assertEqual([[6, False, ref_id]], data.get('ref_doctor_ids'))

        # Scenario 2: Evaluate doctors and read them
        self.assertTrue(self.doctor_pool.evaluate_doctors_dict(cr, uid, data))
        self.assertEqual([[6, False, con_id]], data.get('con_doctor_ids'))
        self.assertEqual([[6, False, ref_id]], data.get('ref_doctor_ids'))

        # Scenario 3: Evaluate without doctors
        self.assertFalse(self.doctor_pool.evaluate_doctors_dict(cr, uid, {}))

        # Scenario 4: Evaluate unevaluable data
        self.assertFalse(self.doctor_pool.evaluate_doctors_dict(
            cr, uid, {'doctors': "[(//yy3)]"}))

        # Scenario 5: Use non unique code
        doctors = """[{
            'type': 'c',
            'code': '000',
        }]"""
        data = {'doctors': doctors}
        self.assertTrue(self.doctor_pool.evaluate_doctors_dict(cr, uid, data))

    def test_02_create(self):
        cr, uid = self.cr, self.uid

        user_id = self.user_pool.create(cr, uid, {'name': 'User01',
                                                  'login': 'u01',
                                                  'password': 'u01'})
        self.assertTrue(self.doctor_pool.create(cr, uid, {'name': 'User01',
                                                          'user_id': user_id}))

    def test_03_write(self):
        cr, uid = self.cr, self.uid

        self.assertTrue(self.doctor_pool.write(cr, uid, self.doctors[1],
                                               {'code': '001'}))
