# -*- coding: utf-8 -*-

import logging

from openerp.osv import orm, fields
from openerp import SUPERUSER_ID

from openerp.addons.nh_activity.activity import except_if

_logger = logging.getLogger(__name__)

class nh_clinical_device_category(orm.Model):
    _name = 'nh.clinical.device.category'

    _columns = {
        'name': fields.char("Device Category", size=200),
        'flow_direction': fields.selection([('none', 'None'), ('in', 'In'), ('out', 'Out'), ('both', 'Both')], 'Flow Direction')
    }


class nh_clinical_device_type(orm.Model):
    _name = 'nh.clinical.device.type'
    _columns = {
        'category_id': fields.many2one('nh.clinical.device.category', "Device Category"),
        'name': fields.char('Name', size=100)
    }


class nh_clinical_device(orm.Model):
    _name = 'nh.clinical.device'
    _columns = {
        'type_id': fields.many2one('nh.clinical.device.type', "Device Type"),
        'category_id': fields.related('type_id', 'category_id', type='many2one', relation='nh.clinical.device.category', string='Category'),
        'serial_number': fields.char('Serial Number', size=200),
        'is_available': fields.boolean('Is Available?'),
    }

    _defaults = {
        'is_available': True
    }

    def name_get(self, cr, uid, ids, context):
        res = []
        for device in self.browse(cr, uid, ids, context):
            res.append((device.id, "%s/%s" % (device.type_id.name, device.serial_number)))
        return res


class nh_clinical_device_session(orm.Model):
    _name = 'nh.clinical.device.session'
    _description = 'Device Session'
    _inherit = ['nh.activity.data']
    _rec_name = 'device_id'
    _columns = {
        'device_type_id': fields.many2one('nh.clinical.device.type', 'Device Type', required=True),
        'device_category_id': fields.related('device_type_id', 'category_id', type='many2one', relation='nh.clinical.device.category', string='Device Category'),
        'device_id': fields.many2one('nh.clinical.device', 'Device'),
        'location': fields.char('Location', size=50),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
        'removal_reason': fields.char('Removal reason', size=100),
        'planned': fields.selection((('planned', 'Planned'), ('unplanned', 'Unplanned')), 'Planned?')
    }
    
    def name_get(self, cr, uid, ids, context):
        res = []
        for session in self.browse(cr, uid, ids, context):
            res.append((session.id, "%s/%s" % (session.patient_id.full_name, session.device_type_id.name)))
        return res
    
    def start(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context)
        if activity.data_ref.device_id:
            device_pool = self.pool['nh.clinical.device']
            device_pool.write(cr, uid, activity.data_ref.device_id.id, {'is_available': False})
        super(nh_clinical_device_session, self).start(cr, uid, activity_id, context)
        
    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context)
        if activity.data_ref.device_id:
            device_pool = self.pool['nh.clinical.device']
            device_pool.write(cr, uid, activity.data_ref.device_id.id, {'is_available': True})
        super(nh_clinical_device_session, self).complete(cr, uid, activity_id, context)        
        
    
class nh_clinical_device_connect(orm.Model):
    _name = 'nh.clinical.device.connect'
    _inherit = ['nh.activity.data']
    _description = 'Connect Device'
    _columns = {
        'device_type_id': fields.many2one('nh.clinical.device.type', 'Device Type', required=True),
        'device_id': fields.many2one('nh.clinical.device', 'Device'),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        device_pool = self.pool['nh.clinical.device']
        except_if(not vals.get('patient_id'), msg="Patient missing in submitted values!")
        except_if(not (vals.get('device_id') or vals.get('device_type_id')), msg="Device information missing in submitted values!")
        vals_copy = vals.copy()
        if vals.get('device_id'):
            device = device_pool.browse(cr, uid, vals['device_id'], context=context)
            vals_copy.update({'device_type_id': device.type_id.id})
        return super(nh_clinical_device_connect, self).submit(cr, uid, activity_id, vals_copy, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        api_pool = self.pool['nh.clinical.api']
        device_session_pool = self.pool['nh.clinical.device.session']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        spell_activity_id = api_pool.get_patient_spell_activity_id(cr, uid, activity.data_ref.patient_id.id)
        except_if(not spell_activity_id, msg="No started spell found for patient_id=%s" % activity.data_ref.patient_id.id)
        session_activity_id = device_session_pool.create_activity(cr, uid, 
                                            {'creator_id': activity_id, 'parent_id': spell_activity_id},
                                            {'patient_id': activity.data_ref.patient_id.id,
                                             'device_type_id': activity.data_ref.device_type_id.id,
                                             'device_id': activity.data_ref.device_id.id if activity.data_ref.device_id else False})
        activity_pool.start(cr, uid, session_activity_id)
        return super(nh_clinical_device_connect, self).complete(cr, SUPERUSER_ID, activity_id, context)

class nh_clinical_device_disconnect(orm.Model):
    _name = 'nh.clinical.device.disconnect'
    _inherit = ['nh.activity.data']
    _description = 'Disconnect Device'
    _columns = {
        'device_type_id': fields.many2one('nh.clinical.device.type', 'Device Type', required=True),
        'device_id': fields.many2one('nh.clinical.device', 'Device'),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        device_pool = self.pool['nh.clinical.device']
        except_if(not vals.get('patient_id'), msg="Patient missing in submitted values!")
        except_if(not (vals.get('device_id') or vals.get('device_type_id')), msg="Device information missing in submitted values!")
        vals_copy = vals.copy()
        if vals.get('device_id'):
            device = device_pool.browse(cr, uid, vals['device_id'], context=context)
            vals_copy.update({'device_type_id': device.type_id.id})
        return super(nh_clinical_device_disconnect, self).submit(cr, uid, activity_id, vals_copy, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        api_pool = self.pool['nh.clinical.api']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        spell_activity_id = api_pool.get_patient_spell_activity_id(cr, uid, activity.data_ref.patient_id.id)
        except_if(not spell_activity_id, msg="No started spell found for patient_id=%s" % activity.data_ref.patient_id.id)
        session_activity_id = api_pool.get_device_session_activity_id(cr, uid, activity.data_ref.patient_id.id, activity.data_ref.device_type_id.id)
        except_if(not session_activity_id, msg="No started session found for device_type_id=%s" % activity.data_ref.device_type_id.id)
        activity_pool.complete(cr, uid, session_activity_id)
        return super(nh_clinical_device_disconnect, self).complete(cr, SUPERUSER_ID, activity_id, context)

    
class nh_clinical_device_observation(orm.Model):
    _name = 'nh.clinical.device.observation'
    _inherit = ['nh.activity.data']
    _description = 'Device Observation'
    _columns = {
        'device_id': fields.many2one('nh.clinical.device', 'Device', required=True),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
    }
