from openerp.osv import orm, fields


class test_activity_data_model(orm.Model):
    """
    Test Activity Data Model: TEST purposes only. Will be used to make sure activity+data_model structure works.
    """
    _name = 'test.activity.data.model'
    _inherit = ['nh.activity.data']
    _description = 'Test Activity Model'
    
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


class test_activity_data_model2(orm.Model):
    """
    Test Activity Data Model: TEST purposes only. Will be used to make sure activity+data_model structure works.
    """
    _name = 'test.activity.data.model2'
    _inherit = ['nh.activity.data']

    _columns = {
        'field1': fields.text('Field1')
    }