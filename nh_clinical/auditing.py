import logging

from openerp.osv import orm, fields, osv

_logger = logging.getLogger(__name__)


class nh_clinical_location_activate(orm.Model):
    """
    This Activity is meant to audit the activation of a Location.
    location_id: Location that is going to be activated by the activity complete method.
    """
    _name = 'nh.clinical.location.activate'
    _inherit = ['nh.activity.data']
    _description = "Activate Location"

    _columns = {
        'location_id': fields.many2one('nh.clinical.location', 'Location'),
        'location_name': fields.related('location_id', 'full_name', type='char', size=150, string='Location')
    }

    _order = 'id desc'

    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        location_pool = self.pool['nh.clinical.location']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        if not activity.location_id:
            raise osv.except_osv('Error!', 'There is no location to activate!')
        res = super(nh_clinical_location_activate, self).complete(cr, uid, activity_id, context=context)
        location_pool.write(cr, uid, activity.location_id.id, {'active': True}, context=context)
        return res


class nh_clinical_location_deactivate(orm.Model):
    """
    This Activity is meant to audit the deactivation of a Location.
    location_id: Location that is going to be deactivated by the activity complete method.
                * A Location cannot be deactivated if there is a patient using it.
    """
    _name = 'nh.clinical.location.deactivate'
    _inherit = ['nh.activity.data']
    _description = "Deactivate Location"

    _columns = {
        'location_id': fields.many2one('nh.clinical.location', 'Location'),
        'location_name': fields.related('location_id', 'full_name', type='char', size=150, string='Location')
    }

    _order = 'id desc'

    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        location_pool = self.pool['nh.clinical.location']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        if not activity.location_id:
            raise osv.except_osv('Error!', 'There is no location to deactivate!')
        if activity.location_id.active and not activity.location_id.is_available:
            raise osv.except_osv('Error!', "Can't deactivate a location that is being used.")
        res = super(nh_clinical_location_deactivate, self).complete(cr, uid, activity_id, context=context)
        location_pool.write(cr, uid, activity.location_id.id, {'active': False}, context=context)
        return res


class nh_clinical_user_responsibility_allocation(orm.Model):
    """
    This activity is meant to audit the allocation of responsibility of users to locations.
    responsible_user_id: User we are going to assign responsibility to.
    location_ids: list of location ids we are assigning to the user.
    """
    _name = 'nh.clinical.user.responsibility.allocation'
    _inherit = ['nh.activity.data']
    _description = "Assign User Locations Responsibility"

    _columns = {
        'responsible_user_id': fields.many2one('res.users', 'User'),
        'location_ids': fields.many2many('nh.clinical.location',
                                         'user_allocation_location_rel',
                                         'user_allocation_id', 'location_id', string='Locations'),
    }

    _order = 'id desc'

    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        location_pool = self.pool['nh.clinical.location']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        if not activity.data_ref:
            raise osv.except_osv('Error!', "Can't complete the activity without data!")
        if not activity.data_ref.responsible_user_id:
            raise osv.except_osv('Error!', "Can't complete the activity without selecting a responsible user for the selected locations.")
        res = super(nh_clinical_user_responsibility_allocation, self).complete(cr, uid, activity_id, context=context)

        locations = []
        if any([g.name in ['NH Clinical Ward Manager Group', 'NH Clinical Senior Manager Group']
                for g in activity.data_ref.responsible_user_id.groups_id]):
            for loc in activity.data_ref.location_ids:
                if loc.usage == 'ward':
                    locations.append(loc.id)
                else:
                    locations += location_pool.search(cr, uid, [['id', 'child_of', loc.id]], context=context)
        else:
            for loc in activity.data_ref.location_ids:
                locations += location_pool.search(cr, uid, [['id', 'child_of', loc.id]], context=context)
        vals = {'location_ids': [[6, False, list(set(locations))]]}

        user_pool = self.pool['res.users']
        user_pool.write(cr, uid, activity.data_ref.responsible_user_id.id, vals, context=context)
        return res