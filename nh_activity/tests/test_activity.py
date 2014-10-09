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



class ActivityTest(common.SingleTransactionCase):
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
        activity_pool = self.registry('nh.activity')
        user_pool = self.registry('res.users')
        imd_pool = self.registry('ir.model.data')
        
        super(ActivityTest, self).setUp()

    def test_event_handlers(self):
        test_pool = self.registry('test.activity.data.model')
        activity_pool = self.registry('nh.activity')
        activity_id = self.create_activity('nh.activity.data')
        
        activity_pool._register_handler('nh.activity.data', 'complete', 'test.activity.data.model', 'handle_data_complete')
        activity_pool._register_handler('nh.activity.data', 'start', 'test.activity.data.model', 'handle_data_start')        
        
        assert not test_pool._start_handler_event
        assert not test_pool._complete_handler_event
        
        self.start(activity_id)
        self.complete(activity_id)
        
        assert test_pool._start_handler_event
        assert test_pool._start_handler_event.model._name == 'nh.activity.data'
        assert test_pool._start_handler_event.method == 'start'
        assert test_pool._start_handler_event.activity.data_model == 'nh.activity.data'
        
        assert test_pool._complete_handler_event
        assert test_pool._complete_handler_event.model._name == 'nh.activity.data'
        assert test_pool._complete_handler_event.method == 'complete'
        assert test_pool._complete_handler_event.activity.data_model == 'nh.activity.data'
               
    def test_activity(self):
        self.assertTrue( test_pool._name == 'test.activity.data.model', 'test model not found')
        self.assertTrue( 'field1' in test_pool._columns.keys(), 'field1 not found in test model')
        
        activity_id = self.create_activity('test.activity.data.model', {}, {'field1': 'test1'})
        self.transitions_test(activity_id)
        res = activity_pool.activity_rank_map(cr, uid)
#         print res
        
    def create_activity(self, model, activity_vals={}, data_vals={}):
        model_pool = self.registry(model) 
        activity_id = model_pool.create_activity(cr, uid, activity_vals, data_vals)
        activity = activity_pool.browse(cr, uid, activity_id)
        _logger.warn("Testing 'create_activity' method...")
        self.assertTrue(activity_id, 'activity_id is None')
        self.assertTrue(activity.data_model == model, 'wrong data model')
        self.assertTrue(activity.state == 'new', 'state != new')
        return activity_id
    
    def transitions_test(self, activity_id):
        activity = activity_pool.browse(cr, uid, activity_id)
        model_pool = self.registry(activity.data_model)
        # transitions: new - schedule - start - complete - cancel
        # + submit, assign, unassign
        model_pool._transitions = {
            'new': ['schedule', 'plan', 'start', 'complete', 'cancel', 'submit', 'assign', 'unassign', 'retrieve','validate'],
            'planned': ['schedule', 'start', 'complete', 'cancel', 'submit', 'assign', 'unassign', 'retrieve', 'validate'],
            'scheduled': ['start', 'complete', 'cancel', 'submit', 'assign', 'unassign', 'retrieve', 'validate'],
            'started': ['complete', 'cancel', 'submit', 'assign', 'unassign', 'retrieve', 'validate'],
            'completed': ['retrieve', 'validate'],
            'cancelled': ['retrieve', 'validate']
        }
        # test from state = new
        state_method_map = {'new': 'new',
                            'planned': 'plan',
                            'scheduled': 'schedule',
                            'started': 'start',
                            'completed': 'complete',
                            'cancelled': 'cancel'}
        kwargs = {}
        
        kwargs.update({'vals': {'field1': 'test value'}}) # submit vals
        kwargs.update({'user_id': self.create_user(**kwargs)})
        paths = [
                 ['new', 'planned', 'scheduled', 'started', 'completed'],
                 ['new', 'planned', 'scheduled', 'started', 'cancelled']
                 ]
        # state_method_map.keys() - doesn't keep initial keys order, so we get transition from scheduled to new
        for path in paths:
            savepoint_name_path = self.savepoint_create()
            for state in path:
                state_method = state_method_map[state]
                if hasattr(self, state_method):
                    #import pdb; pdb.set_trace()
                    try:
                        eval("self.%s(activity_id, **kwargs)" % state_method)
                    except:
                        assert False, "Test failed for state_method %s" % state_method
                    for method in model_pool._transitions[state]: 
                        if hasattr(self, method):
                            savepoint_name = self.savepoint_create()
                            try:
                                eval("self.%s(activity_id, **kwargs)" % method)    
                            except:                      
                                assert False, "Test failed for method '%s' in state '%s'" % (method, state)
                            self.assertTrue((model_pool.is_action_allowed(state, method)), 
                                            "wrong result from is_action_allowed, method '%s' state '%s'" % (method, state))                              
                            self.savepoint_rollback(savepoint_name)
            self.savepoint_rollback(savepoint_name_path)                

    def create_user(self, **kwargs):
        fake.seed(next_seed())
        group = imd_pool.get_object(cr, uid, "base", "group_system")
        #import pdb; pdb.set_trace()
        first_name = fake.first_name()
        last_name = fake.last_name()
        vals = {
            'name': kwargs.get('name') or "%s %s" % (first_name, last_name),
            'login': kwargs.get('login') or first_name.lower(),
            'password': kwargs.get('password') or first_name.lower(),
            'groups_id': kwargs.get('groups_id') or [(4, group.id)],

        }  
        res = user_pool.create(cr, uid, vals)
        return res        

    def unassign(self, activity_id, **kwargs):
        activity = activity_pool.browse(cr, uid, activity_id)
        if not activity.user_id:
            _logger.warn("Unassign: activity is not assigned, trying to assign...")
            user_id = kwargs.get('user_id')
            assert user_id, "user_id must be in kwargs"            
            model_pool = self.registry(activity.data_model)
            if 'assign' in model_pool._transitions[activity.state]:
                retval = self.assign(activity_id, **kwargs)
                _logger.warn("Unassign: back to 'unassign', 'assign' returned %s" % retval)
            else:
                _logger.warn("Unassign: activity is not assigned and 'assign' is disabled for state '%s'. Returning positive result." % activity.state)
                return True
        res = False
        try:
            activity_pool.unassign(cr, uid, activity_id)
        except:
            res = False
        else:
            _logger.info("Testing 'unassign' method...")
            res = True
            activity = activity_pool.browse(cr, uid, activity_id)
            self.assertTrue(not activity.user_id, "activity.user_id is set ")
            #import pdb; pdb.set_trace()
        return res 

    def assign(self, activity_id, **kwargs):
        res = False
        user_id = kwargs.get('user_id')
        assert user_id, "user_id must be in kwargs"
        activity = activity_pool.browse(cr, uid, activity_id)
        if activity.user_id:
            _logger.warn("Assign: activity is assigned, trying to unassign...")
            model_pool = self.registry(activity.data_model)
            if 'unassign' in model_pool._transitions[activity.state]:
                retval = self.unassign(activity_id, **kwargs)
                _logger.warn("Assign: back to 'assign', 'unassign' returned %s" % retval)
            else:
                _logger.warn("Assign: activity is assigned and 'unassign' is disabled for state '%s'. Returning positive result." % activity.state)
                return True        
        try:
            activity_pool.assign(cr, uid, activity_id, user_id)
        except:
            res = False
        else:
            _logger.info("Testing 'assign' method...")
            res = True
            activity = activity_pool.browse(cr, uid, activity_id)
            self.assertTrue(activity.user_id.id == user_id, "activity.user_id != user_id ")
            #import pdb; pdb.set_trace()
        return res          
        
    def savepoint_create(self, name=None):
        next_seed()
        i = 0
        while i < 1000:
            try:
                name = name or fake.first_name().lower()
                cr.execute("savepoint %s" % name)
                break
            except:
                pass
        assert i < 1000, "Couldn't create savepoint after 1000 attempts!"
            
        return name
    
    def savepoint_rollback(self, name):
        cr.execute("rollback to savepoint %s" % name)
        return True
    
    def savepoint_release(self, name):
        cr.execute("release savepoint %s" % name)
        return True   

    def submit(self, activity_id, **kwargs):
        res = False
        vals = kwargs.get('vals')
        assert vals, "'vals' must be passed in kwargs!"
        try:
            activity_pool.submit(cr, uid, activity_id, vals)
        except:
            res = False
        else:
            _logger.info("Testing 'submit' method...")
            res = True
            activity = activity_pool.browse(cr, uid, activity_id)
            model_pool = self.registry(activity.data_model)
            # test data model values
            for field in vals.keys():
                value = None
                if model_pool._columns[field] == 'many2many':
                    pass
                elif model_pool._columns[field] == 'one2many':
                    pass
                elif model_pool._columns[field] == 'reference':
                    pass        
                else: # simple fields
                    value = eval("activity.data_ref.%s" % field)
                
                self.assertTrue(vals[field] == value or value is None, "activity.data_ref.field != vals[field]")
        return res 

    
    def new(self, activity_id, **kwargs):
        
        return True
    
    def schedule(self, activity_id, **kwargs):
        next_seed()
        date_scheduled = kwargs.get('date_scheduled') or fake.date_time_between(start_date="1d", end_date="3d").strftime("%Y-%m-%d %H:%M:%S")
        res = False
        try:
            activity_pool.schedule(cr, uid, activity_id, date_scheduled)
        except:
            res = False
        else:
            _logger.info("Testing 'schedule' method...")
            res = True
            activity = activity_pool.browse(cr, uid, activity_id)
            model_pool = self.registry(activity.data_model)
            self.assertTrue(activity.state == 'scheduled', "activity.state != scheduled ")
            self.assertTrue(activity.date_scheduled == date_scheduled, "activity.date_scheduled != date_scheduled ")


        return res

    def start(self, activity_id, **kwargs):
        res = False
        try:
            activity_pool.start(cr, uid, activity_id)
        except:
            res = False
        else:
            _logger.info("Testing 'start' method...")
            res = True
            activity = activity_pool.browse(cr, uid, activity_id)
            self.assertTrue(activity.state == 'started', "activity.state != started ")
            self.assertTrue(activity.date_started, "activity.date_started is none ")
            #import pdb; pdb.set_trace()
        return res            

    def complete(self, activity_id, **kwargs):
        res = False
        try:
            activity_pool.complete(cr, uid, activity_id)
        except:
            res = False
        else:
            _logger.info("Testing 'complete' method...")
            res = True
            activity = activity_pool.browse(cr, uid, activity_id)
            self.assertTrue(activity.state == 'completed', "activity.state != completed ")
            self.assertTrue(activity.date_terminated, "activity.date_terminated is none ")
            #import pdb; pdb.set_trace()
        return res             
            
    def cancel(self, activity_id, **kwargs):
        res = False
        try:
            activity_pool.cancel(cr, uid, activity_id)
        except:
            res = False
        else:
            _logger.info("Testing 'cancel' method...")
            res = True
            activity = activity_pool.browse(cr, uid, activity_id)
            self.assertTrue(activity.state == 'cancelled', "activity.state != cancelled ")
            self.assertTrue(activity.date_terminated, "activity.date_terminated is none ")
            #import pdb; pdb.set_trace()
        return res              
            
            

        