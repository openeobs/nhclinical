# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
"""
``auditing.py`` defines some activity types to audit some specific
operations that are not represented by any other objects in the system
but still need to be audittable.
"""
import logging

from openerp.osv import orm, fields, osv

_logger = logging.getLogger(__name__)


class nh_clinical_location_activate(orm.Model):
    """
    Activity is meant to audit the activation of a Location.
    ``location_id`` is the location that is going to be activated by
    the activity complete method.
    """
    _name = 'nh.clinical.location.activate'
    _inherit = ['nh.activity.data']
    _description = "Activate Location"

    _columns = {
        'location_id': fields.many2one('nh.clinical.location', 'Location'),
        'location_name': fields.related(
            'location_id', 'full_name', type='char', size=150,
            string='Location')
    }

    _order = 'id desc'

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        sets the activity `active` parameter as ``True``.
        """
        activity_pool = self.pool['nh.activity']
        location_pool = self.pool['nh.clinical.location']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        if not activity.location_id:
            raise osv.except_osv('Error!', 'There is no location to activate!')
        res = super(nh_clinical_location_activate, self).complete(
            cr, uid, activity_id, context=context)
        location_pool.write(cr, uid, activity.location_id.id, {'active': True},
                            context=context)
        return res


class nh_clinical_location_deactivate(orm.Model):
    """
    This Activity is meant to audit the deactivation of a Location.
    ``location_id`` is the location that is going to be deactivated by
    the activity complete method.

    A Location cannot be deactivated if there is a patient using it.
    """
    _name = 'nh.clinical.location.deactivate'
    _inherit = ['nh.activity.data']
    _description = "Deactivate Location"

    _columns = {
        'location_id': fields.many2one('nh.clinical.location', 'Location'),
        'location_name': fields.related('location_id', 'full_name',
                                        type='char', size=150,
                                        string='Location')
    }

    _order = 'id desc'

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        sets the activity `active` parameter as ``False``.
        """

        activity_pool = self.pool['nh.activity']
        location_pool = self.pool['nh.clinical.location']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        if not activity.location_id:
            raise osv.except_osv(
                'Error!', 'There is no location to deactivate!')
        if activity.location_id.active and not \
                activity.location_id.is_available:
            raise osv.except_osv(
                'Error!', "Can't deactivate a location that is being used.")
        res = super(nh_clinical_location_deactivate, self).complete(
            cr, uid, activity_id, context=context)
        location_pool.write(cr, uid, activity.location_id.id,
                            {'active': False}, context=context)
        return res
