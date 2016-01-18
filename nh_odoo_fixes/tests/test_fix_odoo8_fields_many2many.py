# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase


class TestNewSet(TransactionCase):

    def setUp(self):
        super(TestNewSet, self).setUp()
        cr, uid = self.cr, self.uid
        self.a_pool = self.registry('test_model_a')
        self.b_pool = self.registry('test_model_b')

        self.b_id = self.b_pool.create(cr, uid, {'name': 'b_name'})
        self.b1_id = self.b_pool.create(cr, uid, {'name': 'b1_name'})
        self.a_id = self.a_pool.create(cr, uid, {'name': 'a_name'})

    def test_new_set_removes_duplicate_ids(self):
        cr, uid = self.cr, self.uid

        self.a_pool.write(cr, uid, [self.a_id], {'a_ids': [
            [6, False, [self.b_id, self.b_id, self.b1_id]]]})
        # test that the many2many junction table 'b_a_rel'
        # contains no duplicates
        cr.execute("SELECT COUNT(*) "
                   "FROM b_a_rel "
                   "WHERE test_model_b_id = %i" % self.b_id)
        num_records = cr.fetchall()
        self.assertEquals(len(num_records), 1)
