# Part of NHClincal. See LICENSE file for full copyright and licensing details.
from openerp.osv import orm, fields


class test_activity_data_model(orm.Model):
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
    _name = 'test.activity.data.model2'
    _inherit = ['nh.activity.data']

    _columns = {
        'field1': fields.text('Field1')
    }
