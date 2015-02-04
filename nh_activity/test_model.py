from openerp.osv import orm, fields


class test_activity_data_model(orm.Model):
    _name = 'test.activity.data.model'
    _inherit=['nh.activity.data']
    
    _columns = {
        'field1': fields.text('Field1')
        
    }

    def __init__(self, pool, cr):
        activity_model = pool['nh.activity']

        super(test_activity_data_model, self).__init__(pool, cr)
    
    _start_handler_event = False
    _complete_handler_event = False

    def handle_data_complete(self, cr, uid, event):
        self._complete_handler_event = event

    def handle_data_start(self, cr, uid, event):
        self._start_handler_event = event
