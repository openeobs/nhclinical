# -*- coding: utf-8 -*-

import logging

from openerp.osv import orm, fields, osv
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class nh_clinical_device_category(orm.Model):
    """
    Represents a device category which groups several types into it.
    """
    _name = 'nh.clinical.device.category'

    _columns = {
        'name': fields.char("Device Category", size=200),
        'flow_direction': fields.selection([('none', 'None'), ('in', 'In'), ('out', 'Out'), ('both', 'Both')], 'Flow Direction')
    }


class nh_clinical_device_type(orm.Model):
    """
    Represents the specific device type of a device instance.
    """
    _name = 'nh.clinical.device.type'
    _columns = {
        'category_id': fields.many2one('nh.clinical.device.category', "Device Category"),
        'name': fields.char('Name', size=100)
    }


class nh_clinical_device(orm.Model):
    """
    Represents a physical device instance.
    """
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

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for device in self.browse(cr, uid, ids, context):
            res.append((device.id, "%s/%s" % (device.type_id.name, device.serial_number)))
        return res


class nh_clinical_device_session(orm.Model):
    """
    Represents the usage of a device in a patient spell.
    """
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

    def start(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context)
        if activity.data_ref.device_id:
            device_pool = self.pool['nh.clinical.device']
            device_pool.write(cr, uid, activity.data_ref.device_id.id, {'is_available': False})
        return super(nh_clinical_device_session, self).start(cr, uid, activity_id, context)
        
    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context)
        if activity.data_ref.device_id:
            device_pool = self.pool['nh.clinical.device']
            device_pool.write(cr, uid, activity.data_ref.device_id.id, {'is_available': True})
        return super(nh_clinical_device_session, self).complete(cr, uid, activity_id, context)

    def get_activity_id(self, cr, uid, patient_id, device_type_id, context=None):
        domain = [
            ['patient_id', '=', patient_id],
            ['device_type_id', '=', device_type_id],
            ['activity_id.state', '=', 'started']]
        session_id = self.search(cr, uid, domain, context=context)
        if not session_id:
            return False
        if len(session_id) > 1:
            _logger.warn("For device_type_id=%s found more than 1 started device session activity_ids"
                         % device_type_id)
        device_session = self.browse(cr, uid, session_id[0], context=context)
        return device_session.activity_id.id
        
    
class nh_clinical_device_connect(orm.Model):
    """
    Represents the action of connecting a device to a patient.
    """
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
        activity_pool = self.pool['nh.activity']
        if not vals.get('patient_id'):
            raise osv.except_osv('Device Connect Error!', "Patient missing in submitted values!")
        if not (vals.get('device_id') or vals.get('device_type_id')):
            raise osv.except_osv('Device Connect Error!', "Device information missing in submitted values!")
        vals_copy = vals.copy()
        if vals.get('device_id'):
            device = device_pool.browse(cr, uid, vals['device_id'], context=context)
            if not device.is_available:
                raise osv.except_osv('Device Connect Error!', "This device is already being used!")
            vals_copy.update({'device_type_id': device.type_id.id})
        spell_pool = self.pool['nh.clinical.spell']
        spell_id = spell_pool.get_by_patient_id(cr, uid, vals.get('patient_id'), context=context)
        if not spell_id:
            raise osv.except_osv('Device Connect Error!',
                                 'No started spell found for patient_id=%s' % vals.get('patient_id'))
        spell_activity_id = spell_pool.browse(cr, uid, spell_id, context=context).activity_id.id
        activity_pool.write(cr, uid, activity_id, {'parent_id': spell_activity_id}, context=context)
        return super(nh_clinical_device_connect, self).submit(cr, uid, activity_id, vals_copy, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        spell_pool = self.pool['nh.clinical.spell']
        device_session_pool = self.pool['nh.clinical.device.session']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        spell_id = spell_pool.get_by_patient_id(cr, uid, activity.data_ref.patient_id.id, context=context)
        spell_activity_id = spell_pool.browse(cr, uid, spell_id, context=context).activity_id.id
        session_activity_id = device_session_pool.create_activity(cr, uid, {
            'creator_id': activity_id, 'parent_id': spell_activity_id
        }, {
            'patient_id': activity.data_ref.patient_id.id, 'device_type_id': activity.data_ref.device_type_id.id,
            'device_id': activity.data_ref.device_id.id if activity.data_ref.device_id else False
        }, context=context)
        activity_pool.start(cr, uid, session_activity_id, context=context)
        return super(nh_clinical_device_connect, self).complete(cr, SUPERUSER_ID, activity_id, context=context)


class nh_clinical_device_disconnect(orm.Model):
    """
    Represents the action of disconnecting a device from a patient.
    """
    _name = 'nh.clinical.device.disconnect'
    _inherit = ['nh.activity.data']
    _description = 'Disconnect Device'
    _columns = {
        'device_type_id': fields.many2one('nh.clinical.device.type', 'Device Type', required=True),
        'device_id': fields.many2one('nh.clinical.device', 'Device'),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
        'session_activity_id': fields.many2one('nh.activity', 'Disconnected Device Session')
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        device_pool = self.pool['nh.clinical.device']
        activity_pool = self.pool['nh.activity']
        session_pool = self.pool['nh.clinical.device.session']
        if not vals.get('patient_id'):
            osv.except_osv('Device Disconnect Error!', "Patient missing in submitted values!")
        if not (vals.get('device_id') or vals.get('device_type_id')):
            osv.except_osv('Device Disconnect Error!', "Device information missing in submitted values!")
        vals_copy = vals.copy()
        if vals.get('device_id'):
            device = device_pool.browse(cr, uid, vals['device_id'], context=context)
            vals_copy.update({'device_type_id': device.type_id.id})
            session_id = session_pool.search(cr, uid, [
                ['activity_id.state', '=', 'started'], ['device_id', '=', vals.get('device_id')],
                ['patient_id', '=', vals.get('patient_id')]], context=context)
            if not session_id:
                raise osv.except_osv('Device Disconnect Error!',
                                     'No started session found for device_id=%s' % vals_copy.get('device_id'))
            session_activity_id = session_pool.browse(cr, uid, session_id[0], context=context).activity_id.id
        else:
            session_activity_id = session_pool.get_activity_id(cr, uid, vals.get('patient_id'),
                                                               vals_copy.get('device_type_id'), context=context)
            if not session_activity_id:
                raise osv.except_osv('Device Disconnect Error!',
                                     'No started session found for device_type_id=%s' % vals_copy.get('device_type_id'))
        vals_copy.update({'session_activity_id': session_activity_id})
        session_activity = activity_pool.browse(cr, uid, session_activity_id, context=context)
        spell_activity_id = session_activity.parent_id.id if session_activity.parent_id else False
        activity_pool.write(cr, uid, activity_id, {'parent_id': spell_activity_id}, context=context)
        return super(nh_clinical_device_disconnect, self).submit(cr, uid, activity_id, vals_copy, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        activity_pool.complete(cr, uid, activity.data_ref.session_activity_id.id, context=context)
        return super(nh_clinical_device_disconnect, self).complete(cr, SUPERUSER_ID, activity_id, context)

    
class nh_clinical_device_observation(orm.Model):
    _name = 'nh.clinical.device.observation'
    _inherit = ['nh.activity.data']
    _description = 'Device Observation'
    _columns = {
        'device_id': fields.many2one('nh.clinical.device', 'Device', required=True),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
    }
