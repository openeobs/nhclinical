# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
from openerp.osv import orm, fields


class test_activity_data_model0(orm.Model):
    """
    Test Activity Data Model: TEST purposes only.
    Will be used to make sure the activity + data_model structure works.
    """
    _name = 'test.activity.data.model0'
    _inherit = ['nh.activity.data']

    _POLICY = {'activities': [
        {
            'model': 'test.activity.data.model0',
            'type': 'schedule',
            'cancel_others': True,
            'create_data': {
                'field1': 'activity.data_ref.field1',
                'frequency': 'activity.data_ref.frequency'
            },
            'case': 1
        }, {
            'model': 'test.activity.data.model1',
            'type': 'start',
            'cancel_others': True,
            'create_data': {
                'field1': 'activity.data_ref.field1'
            },
            'domains': [
                {
                    'object': 'nh.activity',
                    'domain': [
                        ['data_model', '=', 'test.activity.data.model0'],
                        ['state', '=', 'completed']
                    ]
                }
            ],
            'case': 2,
            'context': 'test2'
        }, {
            'model': 'test.activity.data.model3',
            'type': 'recurring',
            'cancel_others': False,
            'create_data': {
                'field1': 'activity.data_ref.field1',
                'frequency': 'activity.data_ref.frequency'
            },
            'case': 3,
            'context': 'test2'
        }, {
            'model': 'test.activity.data.model4',
            'type': 'complete',
            'cancel_others': False,
            'data': {
                'field1': 'TESTCOMPLETE'
            },
            'case': 4,
            'context': 'test'
        }]}

    _columns = {
        'field1': fields.text('Field1'),
        'frequency': fields.integer('Frequency'),
        'patient_id': fields.many2one('nh.clinical.patient', "Patient")
    }


class test_activity_data_model1(orm.Model):
    """
    Test Activity Data Model: TEST purposes only.
    Will be used to make sure activity + data_model structure works.
    """
    _name = 'test.activity.data.model1'
    _inherit = ['nh.activity.data']

    _POLICY = {}

    _columns = {
        'field1': fields.text('Field1'),
        'patient_id': fields.many2one('nh.clinical.patient', "Patient")
    }


class test_activity_data_model3(orm.Model):
    """
    Test Activity Data Model: TEST purposes only.
    Will be used to make sure activity + data_model structure works.
    """
    _name = 'test.activity.data.model3'
    _inherit = ['nh.activity.data']

    _POLICY = {}

    _columns = {
        'field1': fields.text('Field1'),
        'frequency': fields.integer('Frequency'),
        'patient_id': fields.many2one('nh.clinical.patient', "Patient")
    }


class test_activity_data_model4(orm.Model):
    """
    Test Activity Data Model: TEST purposes only.
    Will be used to make sure activity + data_model structure works.
    """
    _name = 'test.activity.data.model4'
    _inherit = ['nh.activity.data']

    _POLICY = {}

    _columns = {
        'field1': fields.text('Field1'),
        'patient_id': fields.many2one('nh.clinical.patient', "Patient")
    }
