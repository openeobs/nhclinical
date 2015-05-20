from openerp.osv import osv, fields


class allocating_user(osv.TransientModel):
    _name = 'nh.clinical.allocating.user'
    _rec_name = 'user_id'

    def _get_roles(self, cr, uid, ids, field_names, args, context=None):
        res = {}
        for allocating_user in self.browse(cr, uid, ids, context=context):
            group_names = [group.name for group in allocating_user.user_id.groups_id]
            roles = ''
            if 'NH Clinical HCA Group' in group_names:
                roles += 'HCA '
            if 'NH Clinical Nurse Group' in group_names:
                roles += 'Nurse '
            if 'NH Clinical Ward Manager Group' in group_names:
                roles += 'Ward Manager '
            if 'NH Clinical Senior Manager Group' in group_names:
                roles += 'Senior Manager '
            if 'NH Clinical Doctor Group' in group_names:
                roles += 'Doctor '
            res[allocating_user.id] = roles
        return res

    _columns = {
        'user_id': fields.many2one('res.users', 'User', required=1),
        'roles': fields.function(_get_roles, type='char', size=256, string='Roles'),
        'location_ids': fields.many2many('nh.clinical.location', 'allocating_user_rel', 'user_allocating_id',
                                         'location_id', string='Locations')
    }

    def get_domain_location_ids(self, cr, uid, ids, ward_ids, context=None):
        return {'domain': {'location_ids': [('usage', '=', 'bed'), ('parent_id', 'in', ward_ids)]}}

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(allocating_user, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        allocation_pool = self.pool['nh.clinical.user.allocation']
        al_id = allocation_pool.search(cr, uid, [['create_uid', '=', uid]], order='id desc')
        if not al_id or not res['fields'].get('location_ids'):
            return res
        else:
            location_pool = self.pool['nh.clinical.location']
            allocation = allocation_pool.browse(cr, uid, al_id[0], context=context)
            ward_ids = [w.id for w in allocation.ward_ids]
            lids = location_pool.search(cr, uid, [['usage', '=', 'bed'], ['id', 'child_of', ward_ids]], context=context)
            res['fields']['location_ids']['domain'] = [['id', 'in', lids]]
        return res


class user_allocation_wizard(osv.TransientModel):
    _name = 'nh.clinical.user.allocation'

    _stages = [['wards', 'Select Wards'], ['users', 'Select Users'], ['allocation', 'Allocation']]

    _columns = {
        'create_uid': fields.many2one('res.users', 'User Executing the Wizard'),
        'stage': fields.selection(_stages, string='Stage'),
        'ward_ids': fields.many2many('nh.clinical.location', 'allocation_ward_rel', 'allocation_id', 'location_id',
                                     string='Wards', domain=[['usage', '=', 'ward']]),
        'user_ids': fields.many2many('res.users', 'allocation_user_rel', 'allocation_id', 'user_id', string='Users'),
        'allocating_user_ids': fields.many2many('nh.clinical.allocating.user', 'allocating_allocation_rel',
                                                'allocation_id', 'allocating_user_id', string='Allocating Users')
    }
    _defaults = {
        'stage': 'users'
    }

    def submit_users(self, cr, uid, ids, context=None):
        allocating_user_pool = self.pool['nh.clinical.allocating.user']
        wizard = self.browse(cr, uid, ids[0], context=context)
        aluser_ids = [allocating_user_pool.create(cr, uid, {
            'user_id': user.id,
            'location_ids': [[6, 0, [l.id for l in user.location_ids]]]
        }, context=context) for user in wizard.user_ids]
        self.write(cr, uid, ids, {'allocating_user_ids': [[6, 0, aluser_ids]], 'stage': 'allocation'})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Allocation',
            'res_model': 'nh.clinical.user.allocation',
            'res_id': ids[0],
            'view_mode': 'form',
            'target': 'new',
        }

    def complete(self, cr, uid, ids, context=None):
        allocating_user_pool = self.pool['nh.clinical.allocating.user']
        respallocation_pool = self.pool['nh.clinical.user.responsibility.allocation']
        activity_pool = self.pool['nh.activity']
        wizard = self.browse(cr, uid, ids[0], context=context)
        for auser in allocating_user_pool.browse(cr, uid, [u.id for u in wizard.allocating_user_ids], context=context):
            location_ids = [l.id for l in auser.location_ids]
            activity_id = respallocation_pool.create_activity(cr, uid, {}, {
                'responsible_user_id': auser.user_id.id, 'location_ids': [[6, 0, location_ids]]}, context=context)
            activity_pool.complete(cr, uid, activity_id, context=context)
        return {'type': 'ir.actions.act_window_close'}