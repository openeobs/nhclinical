from openerp.osv import orm, fields, osv


class test_activity_data_model(orm.Model):
    _name = 'test.activity.data.model'
    _inherit=['t4.activity.data']
    
    _columns = {
        'field1': fields.text('Field1')
        
    }