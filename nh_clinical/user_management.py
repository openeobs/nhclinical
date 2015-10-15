"""

"""
from openerp.osv import orm, fields, osv


class nh_change_password_wizard(osv.TransientModel):
    """
    Extension of Odoo's res.users change password wizard. Used to allow
    users to change their password securely.
    """
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
    SQL View that shows the users related to clinical roles and allows
    to edit their roles and location responsibilities.
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
        """
        Redirects to the res.users :meth:`create<openerp.models.Model.create>`
        method.

        If ``ward_ids`` is provided, a
        :mod:`responsibility allocation<auditing.nh_clinical_user_responsibility_allocation>`
        is created and completed to assign the user to those wards.

        :returns: res.users id
        :rtype: int
        """
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
        """
        Checks if the user is allowed to execute the action (needs to
        be related to an equal ranking role or greater as the users
        that are being edited) and then redirects to the res.users
        :meth:`write<openerp.models.Model.write>` method.

        If ``ward_ids`` is edited, a
        :mod:`responsibility allocation<auditing.nh_clinical_user_responsibility_allocation>`
        is created and completed to assign the users to those wards.

        :returns: ``True``
        :rtype: bool
        """
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
        if vals.get('ward_ids'):
            user_data.pop('ward_ids', None)
        res = user_pool.write(cr, uid, ids, user_data, context=context)

        if vals.get('ward_ids'):
            locations = vals.get('ward_ids')
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
        """
        Extension of Odoo's ``fields_view_get`` method that returns a
        description of the view in dictionary format. This extension is
        adding a domain limit on the form view ``category_id`` field so
        users can only select roles of the same ranking level or lower
        as the ones they are related to.

        :returns: view description
        :rtype: dict
        """
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
        """
        Writes ``False`` on the users ``active`` field.

        :returns: ``True``
        :rtype: bool
        """
        user_pool = self.pool['res.users']
        if uid in ids:
            raise osv.except_osv('Error!', 'You cannot deactivate yourself!')
        return user_pool.write(cr, uid, ids, {'active': False}, context=context)

    def activate(self, cr, uid, ids, context=None):
        """
        Writes ``True`` on the users ``active`` field.

        :returns: ``True``
        :rtype: bool
        """
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
