from openerp.osv import orm, fields, osv


class nh_change_password_wizard(osv.TransientModel):
    _name = "change.password.wizard"
    _inherit = "change.password.wizard"

    def _default_user_ids(self, cr, uid, context=None):
        if context is None:
            context = {}
        user_model = self.pool['res.users']
        user_ids = context.get('active_ids') or []
        return [
            (0, 0, {'user_id': user.id, 'user_login': user.login})
            for user in user_model.browse(cr, uid, user_ids, context=context)
        ]

    _defaults = {
        'user_ids': _default_user_ids,
    }


class nh_clinical_user_management(orm.Model):
    """
    SQL View that shows the Clinical users and allows to assign roles and responsibilities to them.
    """
    _name = "nh.clinical.user.management"
    _inherits = {'res.users': 'user_id'}
    _auto = False
    _table = "nh_clinical_user_management"
    _ward_ids_not_editable = ['Nurse', 'HCA']

    def _get_ward_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        for user in self.browse(cr, uid, ids, context=context):
            res[user.id] = [loc.id for loc in user.location_ids if loc.usage == 'ward']
        return res

    _columns = {
        'user_id': fields.many2one('res.users', 'User', required=1, ondelete='restrict'),
        'ward_ids': fields.function(_get_ward_ids, type='many2many', relation='nh.clinical.location',
                                    string='Ward Responsibility', domain=[['usage', '=', 'ward']])
    }

    def create(self, cr, uid, vals, context=None):
        user_pool = self.pool['res.users']
        allocation_pool = self.pool['nh.clinical.user.responsibility.allocation']
        activity_pool = self.pool['nh.activity']
        user_data = vals.copy()
        if vals.get('ward_ids'):
            user_data.pop('ward_ids', None)
        user_id = user_pool.create(cr, uid, user_data, context=context)

        if vals.get('ward_ids')[0][2]:
            locations = vals.get('ward_ids')
            user = self.browse(cr, uid, user_id, context=context)
            editable = any([c.name not in self._ward_ids_not_editable for c in user.category_id])
            if not editable:
                raise osv.except_osv('Role Error!', 'This user cannot be assigned with ward responsibility!')
            activity_id = allocation_pool.create_activity(cr, uid, {}, {
                'responsible_user_id': user_id,
                'location_ids': locations}, context=context)
            activity_pool.complete(cr, uid, activity_id, context=context)
        return user_id

    def write(self, cr, uid, ids, vals, context=None):
        user_pool = self.pool['res.users']
        category_pool = self.pool['res.partner.category']
        allocation_pool = self.pool['nh.clinical.user.responsibility.allocation']
        activity_pool = self.pool['nh.activity']
        u = user_pool.browse(cr, uid, uid, context=context)
        category_ids = [c.id for c in u.category_id]
        child_ids = []
        for c in category_ids:
            child_ids += category_pool.get_child_of_ids(cr, uid, c, context=context)
        for user in self.browse(cr, uid, ids, context=context):
            ucids = [c.id for c in user.category_id]
            if any([i for i in ucids if i not in child_ids]):
                raise osv.except_osv('Permission Error!', 'You are not allowed to edit this user!')
        user_data = vals.copy()
        res = user_pool.write(cr, uid, ids, user_data, context=context)

        if vals.get('ward_ids')[0][2]:
            locations = vals.get('ward_ids')
            user_data.pop('ward_ids', None)
            for user in self.browse(cr, uid, ids, context=context):
                editable = any([c.name not in self._ward_ids_not_editable for c in user.category_id])
                if not editable:
                    raise osv.except_osv('Role Error!', 'This user cannot be assigned with ward responsibility!')
            for user_id in ids:
                activity_id = allocation_pool.create_activity(cr, uid, {}, {
                    'responsible_user_id': user_id,
                    'location_ids': locations}, context=context)
                activity_pool.complete(cr, uid, activity_id, context=context)
        return res


    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        ctx = context.copy()
        ctx['partner_category_display'] = 'short'
        res = super(nh_clinical_user_management, self).fields_view_get(cr, user, view_id, view_type, ctx, toolbar, submenu)
        if view_type == 'form' and res['fields'].get('category_id'):
            user_pool = self.pool['res.users']
            category_pool = self.pool['res.partner.category']
            u = user_pool.browse(cr, user, user, context=ctx)
            category_ids = [c.id for c in u.category_id]
            child_ids = []
            for c in category_ids:
                child_ids += category_pool.get_child_of_ids(cr, user, c, context=ctx)
            res['fields']['category_id']['domain'] = [['id', 'in', child_ids]]
        return res

    def allocate_responsibility(self, cr, uid, ids, context=None):
        user = self.browse(cr, uid, ids[0], context=context)
        context.update({'default_user_id': user.id})
        view = {
            'type': 'ir.actions.act_window',
            'res_model': 'nh.clinical.responsibility.allocation',
            'name': 'Location Responsibility Allocation',
            'view_mode': 'form',
            'view_type': 'tree,form',
            'target': 'new',
            'context': context,
        }
        return view

    def deactivate(self, cr, uid, ids, context=None):
        user_pool = self.pool['res.users']
        if uid in ids:
            raise osv.except_osv('Error!', 'You cannot deactivate yourself!')
        return user_pool.write(cr, uid, ids, {'active': False}, context=context)

    def activate(self, cr, uid, ids, context=None):
        user_pool = self.pool['res.users']
        return user_pool.write(cr, uid, ids, {'active': True}, context=context)

    def init(self, cr):
        cr.execute("""
            drop view if exists %s;
            create or replace view %s as (
                select
                    users.id as id,
                    users.id as user_id
                from res_users users
                inner join res_partner partner on partner.id = users.partner_id
            )
        """ % (self._table, self._table))


class nh_clinical_userboard(orm.Model):
    """
    SQL View that shows the NH Clinical users and allows to assign roles and responsibilities to them.
    """
    _name = "nh.clinical.userboard"
    _inherits = {'res.users': 'user_id'}
    _auto = False
    _groups = {'hca': ['NH Clinical HCA Group'],
               'nurse': ['NH Clinical Nurse Group'],
               'ward_manager': ['NH Clinical Ward Manager Group', 'Contact Creation'],
               'senior_manager': ['NH Clinical Senior Manager Group', 'Contact Creation'],
               'doctor': ['NH Clinical Doctor Group']}

    _table = "nh_clinical_userboard"
    _columns = {
        'user_id': fields.many2one('res.users', 'User', required=1, ondelete='restrict'),
        'name': fields.char('Name', size=64, required=True),
        'login': fields.char('Login', size=64, required=True),
        'password': fields.char('Password', size=64),
        'hca': fields.boolean('HCA'),
        'nurse': fields.boolean('Nurse'),
        'ward_manager': fields.boolean('Ward Manager'),
        'senior_manager': fields.boolean('Senior Manager'),
        'doctor': fields.boolean('Doctor')
    }

    def responsibility_allocation(self, cr, uid, ids, context=None):
        user = self.browse(cr, uid, ids[0], context=context)
        context.update({'default_user_id': user.id})
        view = {
            'type': 'ir.actions.act_window',
            'res_model': 'nh.clinical.responsibility.allocation',
            'name': 'Location Responsibility Allocation',
            'view_mode': 'form',
            'view_type': 'tree,form',
            'target': 'new',
            'context': context,
        }
        return view

    def create(self, cr, uid, vals, context=None):
        if not context:
            context = {}
        if not any([vals.get(g) for g in self._groups.keys()]):
            raise osv.except_osv('Error!', 'At least one role must be selected.')
        user_pool = self.pool['res.users']
        groups_pool = self.pool['res.groups']
        user_write_vals = {}
        user_write_vals.update({'name': vals['name']})
        user_write_vals.update({'login': vals['login'], 'password': vals['login']})
        group_names = ['Employee']
        for g in self._groups.keys():
            if vals.get(g):
                group_names += self._groups[g]
        groups = groups_pool.search(cr, uid, [('name', 'in', group_names)], context=context)
        user_write_vals.update({'groups_id': [[6, False, groups]]})
        return user_pool.create(cr, uid, user_write_vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        for user in self.browse(cr, uid, ids, context=context):
            if not any([vals.get(g) if isinstance(vals.get(g), bool) else eval('user.'+g) for g in self._groups.keys()]):
                raise osv.except_osv('Error!', 'At least one role must be selected.')
            user_pool = self.pool['res.users']
            groups_pool = self.pool['res.groups']
            user_write_vals = {}
            if vals.get('name'):
                user_write_vals.update({'name': vals['name']})
            if vals.get('login'):
                user_write_vals.update({'login': vals['login']})
            group_names = ['Employee']
            for g in self._groups.keys():
                check_g = vals.get(g) if isinstance(vals.get(g), bool) else eval('user.'+g)
                if check_g:
                    group_names += self._groups[g]
            groups = groups_pool.search(cr, uid, [('name', 'in', group_names)], context=context)
            user_write_vals.update({'groups_id': [[6, False, groups]]})
            user_pool.write(cr, uid, [user.user_id.id], user_write_vals, context=context)
        return True

    def init(self, cr):
        cr.execute("""
            drop view if exists %s;
            create or replace view %s as (
                with user_groups as (
                    select
                        users.id as id,
                        array_agg(rgroup.name) as groups
                    from res_users users
                    inner join res_groups_users_rel gur on gur.uid = users.id
                    inner join res_groups rgroup on rgroup.id = gur.gid
                    group by users.id
                )
                select
                    users.id as id,
                    users.id as user_id,
                    partner.name as name,
                    users.login as login,
                    users.password as password,
                    case
                        when ug.groups @> '{"NH Clinical HCA Group"}' then true
                        else false
                    end as hca,
                    case
                        when ug.groups @> '{"NH Clinical Nurse Group"}' then true
                        else false
                    end as nurse,
                    case
                        when ug.groups @> '{"NH Clinical Ward Manager Group"}' then true
                        else false
                    end as ward_manager,
                    case
                        when ug.groups @> '{"NH Clinical Senior Manager Group"}' then true
                        else false
                    end as senior_manager,
                    case
                        when ug.groups @> '{"NH Clinical Doctor Group"}' then true
                        else false
                    end as doctor
                from res_users users
                inner join res_partner partner on partner.id = users.partner_id
                inner join user_groups ug on ug.id = users.id
                where ug.groups @> '{"NH Clinical HCA Group"}' or ug.groups @> '{"NH Clinical Nurse Group"}' or ug.groups @> '{"NH Clinical Ward Manager Group"}' or ug.groups @> '{"NH Clinical Senior Manager Group"}' or ug.groups @> '{"NH Clinical Doctor Group"}'
            )
        """ % (self._table, self._table))


class nh_clinical_admin_userboard(orm.Model):
    """
    SQL View that shows the NH Clinical users and allows to assign roles and responsibilities to them. Slightly different
    functionality for the Admin user.
    """
    _name = "nh.clinical.admin.userboard"
    _inherits = {'res.users': 'user_id'}
    _auto = False
    _table = "nh_clinical_admin_userboard"

    _groups = {'hca': ['NH Clinical HCA Group'],
               'nurse': ['NH Clinical Nurse Group'],
               'ward_manager': ['NH Clinical Ward Manager Group', 'Contact Creation'],
               'senior_manager': ['NH Clinical Senior Manager Group', 'Contact Creation'],
               'admin': ['NH Clinical Admin Group', 'Contact Creation'],
               'kiosk': ['NH Clinical Kiosk Group'],
               'doctor': ['NH Clinical Doctor Group']}

    _columns = {
        'user_id': fields.many2one('res.users', 'User', required=1, ondelete='restrict'),
        'name': fields.char('Name', size=64, required=True),
        'login': fields.char('Login', size=64, required=True),
        'password': fields.char('Password', size=64),
        'active': fields.boolean('Active'),
        'hca': fields.boolean('HCA'),
        'nurse': fields.boolean('Nurse'),
        'ward_manager': fields.boolean('Ward Manager'),
        'senior_manager': fields.boolean('Senior Manager'),
        'doctor': fields.boolean('Doctor'),
        'kiosk': fields.boolean('eObs Kiosk'),
        'admin': fields.boolean('Open eObs Administrator')
    }

    def responsibility_allocation(self, cr, uid, ids, context=None):
        user = self.browse(cr, uid, ids[0], context=context)
        context.update({'default_user_id': user.id})
        view = {
            'type': 'ir.actions.act_window',
            'res_model': 'nh.clinical.responsibility.allocation',
            'name': 'Location Responsibility Allocation',
            'view_mode': 'form',
            'view_type': 'tree,form',
            'target': 'new',
            'context': context,
        }
        return view

    def deactivate(self, cr, uid, ids, context=None):
        user_pool = self.pool['res.users']
        if uid in ids:
            raise osv.except_osv('Error!', 'You cannot deactivate yourself!')
        return user_pool.write(cr, uid, ids, {'active': False}, context=context)

    def activate(self, cr, uid, ids, context=None):
        user_pool = self.pool['res.users']
        return user_pool.write(cr, uid, ids, {'active': True}, context=context)

    def create(self, cr, uid, vals, context=None):
        if not context:
            context = {}
        if not any([vals.get(g) for g in self._groups.keys()]):
            raise osv.except_osv('Error!', 'At least one role must be selected.')
        user_pool = self.pool['res.users']
        groups_pool = self.pool['res.groups']
        user_write_vals = {}
        user_write_vals.update({'name': vals['name']})
        user_write_vals.update({'login': vals['login'], 'password': vals['login']})
        group_names = ['Employee']
        for g in self._groups.keys():
            if vals.get(g):
                group_names += self._groups[g]
        groups = groups_pool.search(cr, uid, [('name', 'in', group_names)], context=context)
        user_write_vals.update({'groups_id': [[6, False, groups]]})
        return user_pool.create(cr, uid, user_write_vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        for user in self.browse(cr, uid, ids, context=context):
            if not any([vals.get(g) if isinstance(vals.get(g), bool) else eval('user.'+g) for g in self._groups.keys()]):
                raise osv.except_osv('Error!', 'At least one role must be selected.')
            user_pool = self.pool['res.users']
            groups_pool = self.pool['res.groups']
            user_write_vals = {}
            if vals.get('name'):
                user_write_vals.update({'name': vals['name']})
            if vals.get('login'):
                user_write_vals.update({'login': vals['login']})
            group_names = ['Employee']
            for g in self._groups.keys():
                check_g = vals.get(g) if isinstance(vals.get(g), bool) else eval('user.'+g)
                if check_g:
                    group_names += self._groups[g]
            groups = groups_pool.search(cr, uid, [('name', 'in', group_names)], context=context)
            user_write_vals.update({'groups_id': [[6, False, groups]]})
            user_pool.write(cr, uid, [user.user_id.id], user_write_vals, context=context)
        return True

    def init(self, cr):
        cr.execute("""
            drop view if exists %s;
            create or replace view %s as (
                with user_groups as (
                    select
                        users.id as id,
                        array_agg(rgroup.name) as groups
                    from res_users users
                    inner join res_groups_users_rel gur on gur.uid = users.id
                    inner join res_groups rgroup on rgroup.id = gur.gid
                    group by users.id
                )
                select
                    users.id as id,
                    users.id as user_id,
                    users.active as active,
                    partner.name as name,
                    users.login as login,
                    users.password as password,
                    case
                        when ug.groups @> '{"NH Clinical HCA Group"}' then true
                        else false
                    end as hca,
                    case
                        when ug.groups @> '{"NH Clinical Nurse Group"}' then true
                        else false
                    end as nurse,
                    case
                        when ug.groups @> '{"NH Clinical Ward Manager Group"}' then true
                        else false
                    end as ward_manager,
                    case
                        when ug.groups @> '{"NH Clinical Senior Manager Group"}' then true
                        else false
                    end as senior_manager,
                    case
                        when ug.groups @> '{"NH Clinical Doctor Group"}' then true
                        else false
                    end as doctor,
                    case
                        when ug.groups @> '{"NH Clinical Kiosk Group"}' then true
                        else false
                    end as kiosk,
                    case
                        when ug.groups @> '{"NH Clinical Admin Group"}' then true
                        else false
                    end as admin
                from res_users users
                inner join res_partner partner on partner.id = users.partner_id
                inner join user_groups ug on ug.id = users.id
                where users.id != 1 and (ug.groups @> '{"NH Clinical HCA Group"}' or ug.groups @> '{"NH Clinical Nurse Group"}' or ug.groups @> '{"NH Clinical Ward Manager Group"}' or ug.groups @> '{"NH Clinical Senior Manager Group"}' or ug.groups @> '{"NH Clinical Doctor Group"}' or ug.groups @> '{"NH Clinical Kiosk Group"}' or ug.groups @> '{"NH Clinical Admin Group"}')
            )
        """ % (self._table, self._table))