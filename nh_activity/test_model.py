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


class test_activity_data_model2(orm.Model):
    """
    Test Activity Data Model: TEST purposes only. Will be used to make sure activity+data_model structure works.
    """
    _name = 'test.activity.data.model2'
    _inherit = ['nh.activity.data']

    _columns = {
        'field1': fields.text('Field1')
    }