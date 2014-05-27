from openerp.tests import common
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta as rd
from openerp import tools
from openerp.tools import config 
from openerp.osv import orm, fields, osv

import logging        
from pprint import pprint as pp
_logger = logging.getLogger(__name__)

from faker import Faker
fake = Faker()
seed = fake.random_int(min=0, max=9999999)
def next_seed():
    global seed
    seed += 1
    return seed



class BaseTest(common.SingleTransactionCase):
    @classmethod
    def tearDownClass(cls):
        if config['test_commit']:
            cls.cr.commit()
            print "COMMIT"
        else:
            cls.cr.rollback()
            print "ROLLBACK"
        cls.cr.close()
        
    def setUp(self):
        global cr, uid, seed
        global user_pool, imd_pool, activity_pool, test_pool

        cr, uid = self.cr, self.uid
        test_pool = self.registry('test.activity.data.model')      
        activity_pool = self.registry('t4.activity')
        user_pool = self.registry('res.users')
        imd_pool = self.registry('ir.model.data')
        
        super(BaseTest, self).setUp()
        
    def test_activity_data(self):
        self.assertTrue( test_pool._name == 'test.activity.data.model', 'test model not found')
        self.assertTrue( 'field1' in test_pool._columns.keys(), 'field1 not found in test model')
        
        self.create_activity()
        
        
    def create_activity(self):
        field1 = "test string"
        # data only
        activity_id = test_pool.create_activity(cr, uid, {}, {'field1': field1})
        activity = activity_pool.browse(cr, uid, activity_id)
        self.assertTrue(activity.data_model == 'test.activity.data.model', 'wrong data model')
        self.assertTrue(activity.data_ref.field1 == 'test string', 'wrong data vals ')
        self.assertTrue(activity.data_ref.activity_id.id == activity_id, 'data.activity.id != activity_id')
        self.assertTrue(activity.state == 'new', 'state != new')
        