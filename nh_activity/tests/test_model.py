# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
from openerp.osv import orm, fields


class test_activity_data_model(orm.Model):
    _name = 'test.activity.data.model'
    _inherit = ['nh.activity.data']
    _description = 'Test Activity Model'

    _columns = {
        'field1': fields.text('Field1')
    }


class test_activity_data_model2(orm.Model):
    _name = 'test.activity.data.model2'
    _inherit = ['nh.activity.data']

    _columns = {
        'field1': fields.text('Field1')
    }
