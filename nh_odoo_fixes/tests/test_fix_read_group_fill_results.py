__author__ = 'Will'

from openerp.tests.common import TransactionCase


class TestReadGroupFillResults(TransactionCase):

    def setUp(self):
        super(TestReadGroupFillResults, self).setUp()

        cr, uid = self.cr, self.uid
        self.a_pool = self.registry('test_model_a')
        self.b_pool = self.registry('test_model_b')

        self.b_id = self.b_pool.create(cr, uid, {'name': 'b_name'})
        self.b1_id = self.b_pool.create(cr, uid, {'name': 'b1_name'})
        self.a_id = self.a_pool.create(cr, uid, {'name': 'a_name', 'description': 'a'})

    def test_read_group_fill_results(self):
        cr, uid = self.cr, self.uid

        result = self.a_pool.read_group(cr, uid, [], ['name', 'description'], ['name'])
        self.assertEquals(len(result), 1)
