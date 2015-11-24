# -*- coding: utf-8 -*-
"""
``base`` extends Odoo addons classes and defines core nh_clinical
classes :class:`nh_clinical_context`, :class:`nh_clinical_patient`,
:class:`nh_clinical_location`, :class:`nh_clinical_pos`, etc.
"""

from openerp.osv import orm, fields, osv
from openerp import SUPERUSER_ID
import logging


_logger = logging.getLogger(__name__)


class ir_model_access(orm.Model):
    """
    Extends Odoo's class
    :class:`ir_model_access<openerp.addons.base.ir.ir_model.ir_model_access>`
    which defines write, read, create and unlink permissions for models
    by user group.

    Extension adds field ``perm_responsibility``, which gives permanent
    responsibility to a user group for a model.
    """

    _inherit = 'ir.model.access'
    _columns = {
        'perm_responsibility': fields.boolean('NH Clinical Activity Responsibility'),
        }


# Note - This must go before res_company otherwise a new database will not find the new columns
class res_partner(orm.Model):
    """
    Extends Odoo's class
    :class:`res_partner<openerp.addons.base.res.res_partner.res_partner>`
    which defines a business entity i.e. customer, supplier, employee.

    Extension adds boolean field ``doctor`` and ``code`` for doctor
    type.

    Please note: must precede :class:`res_company` (below) to ensure
    these fields are added to the model in the database.
    """

    _inherit = 'res.partner'
    _columns = {
        'doctor': fields.boolean('Doctor', help="Check this box if this contact is a Doctor"),
        'code': fields.char('Code', size=256),
    }
    _defaults = {
        'notify_email': lambda *args: 'none'
    }

    def create(self, cr, user, vals, context=None):
        """
        Extends Odoo's :meth:`create()<openerp.models.Model.create>`
        to update fields ``group_ids`` and ``doctor_id``.
        """

        return super(res_partner, self).create(
            cr, user, vals,
            context=dict(context or {}, mail_create_nosubscribe=True)
        )


class res_partner_category_extension(orm.Model):
    """
    Extends Odoo's class
    :class:`res_partner_category<openerp.addons.base.res.res_partner.res_partner_category>`
    to add functionality for roles.


    Creates many-to-many relationship between categories (roles) and
    groups, allowing a relation between each role and corresponding
    group(s).

    An example would be the role 'Registrar' belonging to groups base,
    doctor, senior doctor and registrar groups.
    """

    _inherit = 'res.partner.category'
    _columns = {
        'group_ids': fields.many2many('res.groups', 'category_group_rel', 'category_id', 'group_id',
                                      'Related Groups'),
    }

    def name_get(self, cr, user, ids, context=None):
        """
        Extends Odoo's
        :meth:`name_get()<openerp.addons.base.res.res_partner.res_partner_category.name_get>`
        method, fetching the short version of category name belonging
        to ids (without their direct parent).

        :param user: user id
        :type user: int
        :param ids: ids of the categories
        :type ids: list
        :return: categories' display names
        :rtype: list
        """

        if context:
            ctx = context.copy()
        else:
            ctx = {}
        ctx['partner_category_display'] = 'short'
        return super(res_partner_category_extension, self).name_get(cr, user, ids, context=ctx)

    def get_child_of_ids(self, cr, uid, id, context=None):
        """
        Gets all child category ids of parent, recursively.

        :param id: parent id
        :type id: int
        :returns: parent id follow by child ids
        :rtype: list
        """
        res = [id]
        child_ids = self.read(cr, uid, id, ['child_ids'], context=context)['child_ids']
        if not child_ids:
            return res
        else:
            for c in child_ids:
                res += self.get_child_of_ids(cr, uid, c, context=context)
            return res


class res_partner_title_extension(orm.Model):
    """
    Extends Odoo's
    :class:`res_partner_title<openerp.addons.base.res.res_partner.res_partner_title>`
    to include method ``get_title_by_name()``.
    """

    _inherit = 'res.partner.title'

    def get_title_by_name(self, cr, uid, title, create=True, context=None):
        """
        Searches for the title by name. If the title does not exist,
        a new title is created by default.

        :param title: title of partner ('Mr', 'Dr, 'Miss', etc.)
        :type title: string
        :param create: when ``True``, the title will be created if the
            title doesn't exist
        :type create: ``bool`` [default is ``True``]
        :returns: id of title
        :rtype: int
        """

        title = title.replace('.', '').replace(' ', '').lower()
        title_id = self.search(cr, uid, [['name', '=', title]], context=context)
        if not create:
            return title_id[0] if title_id else False
        else:
            if not title_id:
                return self.create(cr, uid, {'name': title}, context=context)
            else:
                return title_id[0]


class res_company(orm.Model):
    """
    Extends Odoo's
    :class:`res_company<openerp.addons.base.res.res_company.res_company>`
    to include one-to-many point of service (pos) field. See
    :class:`nh_clinical_pos`.
    """

    _name = 'res.company'
    _inherit = 'res.company'
    _columns = {
        'pos_ids': fields.one2many('nh.clinical.pos', 'company_id', 'Points of Service'),
    }


class res_users(orm.Model):
    """
    Extends Odoo's
    :class:`res_users<openerp.addons.base.res.res_users.res_users>`
    to include point of service, parent locations of responsibility,
    following patients and the related doctor for the user.
    """

    _name = 'res.users'
    _inherit = 'res.users'
    _columns = {
        'pos_id': fields.many2one('nh.clinical.pos', 'POS'),
        'location_ids': fields.many2many('nh.clinical.location',
                                         'user_location_rel',
                                         'user_id',
                                         'location_id',
                                         'Parent Locations of Responsibility'),
        'following_ids': fields.many2many('nh.clinical.patient',
                                          'user_patient_rel',
                                          'user_id',
                                          'patient_id',
                                          'Following Patients'),
        'doctor_id': fields.many2one('nh.clinical.doctor', 'Related Doctor')
    }

    def check_pos(self, cr, uid, user_id, exception=False, context=None):
        """
        Checks if user has an assigned point of service (POS).

        :param user_id: id of user to check
        :type user_id: int
        :param exception: ``False`` [default]
        :type exception: bool
        :returns: if exception parameter is ``False``, then returns
            ``True`` if POS is defined. Otherwise ``False``. If
            is ``True``, them returns ``True`` if POS is defined. If POS
            is undefined, then
            :class:`osv.except_osv<openerp.osv.osv.except_osv>` is
            raised
        """

        user = self.browse(cr, uid, user_id, context=context)
        result = bool(user.pos_id)
        if not exception:
            return result
        else:
            if not result:
                raise osv.except_osv('Point of Service Not Defined!', 'User %s has no POS defined.' % user.name)
            else:
                return result

    def update_group_vals(self, cr, uid, user_id, vals, context=None):
        """
        Updates a user's groups(see
        :class:`res_partner_category_extension` and :class:`res_groups`)
        for the user.

        :param user_id: id of user
        :type user_id: int
        :param vals: expecting a dictionary with keys ``group_ids``
            and/or ``category_id``. Values will be a list of ints
        :type vals: dict
        :returns: ``True``
        :rtype: bool
        """

        category_pool = self.pool['res.partner.category']
        if not vals.get('category_id'):
            return True
        elif not isinstance(vals.get('category_id'), list):
            raise osv.except_osv('Value Error!', 'category_id field expecting list value, %s received' %
                                 type(vals.get('category_id')))
        elif not isinstance(vals.get('category_id')[0], (list, tuple)):
            raise osv.except_osv('Value Error!', 'many2many update expecting list or tuple value, %s received' %
                                 type(vals.get('category_id')[0]))
        add_groups_id = []
        if not vals.get('groups_id'):
            vals['groups_id'] = []
        for cat_val in vals.get('category_id'):
            if not isinstance(cat_val, (list, tuple)):
                raise osv.except_osv('Value Error!', 'many2many update expecting list or tuple value, %s received' %
                                 type(vals.get('category_id')[0]))
            if cat_val[0] == 3:  # Removing categories / roles
                group_ids = category_pool.read(cr, uid, cat_val[1], ['group_ids'], context=context)['group_ids']
                for gid in group_ids:
                    add_groups_id.append((3, gid))
            elif cat_val[0] == 4:  # Adding categories / roles
                group_ids = category_pool.read(cr, uid, cat_val[1], ['group_ids'], context=context)['group_ids']
                for gid in group_ids:
                    add_groups_id.append((4, gid))
            elif cat_val[0] == 5:  # Removing all categories / roles
                add_groups_id = []
                group_ids = []
                parent_id = category_pool.search(cr, uid, [['name', '=', 'System Administrator']])
                category_ids = category_pool.get_child_of_ids(cr, uid, parent_id[0], context=context)
                for cid in category_ids:
                    group_ids += category_pool.read(cr, uid, cid, ['group_ids'], context=context)['group_ids']
                for gid in group_ids:
                    add_groups_id.append((3, gid))
                vals['groups_id'] += add_groups_id
                return True
            elif cat_val[0] == 6:  # Replacing categories / roles
                add_groups_id = []
                category_ids = cat_val[2]
                new_group_ids = []
                for cid in category_ids:
                    new_group_ids += category_pool.read(cr, uid, cid, ['group_ids'], context=context)['group_ids']
                old_group_ids = self.read(cr, uid, user_id, ['groups_id'], context=context)['groups_id'] if user_id \
                    else []
                for ogid in old_group_ids:
                    is_nhc_related = category_pool.search(cr, uid, [['group_ids', 'in', [ogid]]], context=context)
                    if not is_nhc_related:
                        old_group_ids.remove(ogid)
                group_ids = list(set(old_group_ids + new_group_ids))
                for gid in group_ids:
                    if gid in old_group_ids and gid not in new_group_ids:
                        add_groups_id.append((3, gid))
                    elif gid not in old_group_ids and gid in new_group_ids:
                        add_groups_id.append((4, gid))
                vals['groups_id'] += add_groups_id
                return True
            else:
                raise osv.except_osv('Value Error!', 'Unexpected value for category_id field received: %s' %
                                     cat_val)
        add_groups_id = list(set(add_groups_id))
        if user_id:  # Make sure we don't remove any group from a category the user is still linked to
            old_cat_ids = set(self.read(cr, uid, user_id, ['category_id'], context=context)['category_id'])
            del_cat_ids = [ctuple[1] for ctuple in vals.get('category_id') if ctuple[0] == 3]
            new_cat_ids = [cid for cid in old_cat_ids if cid not in del_cat_ids]
            remaining_group_ids = []
            for cid in new_cat_ids:
                remaining_group_ids += category_pool.read(cr, uid, cid, ['group_ids'], context=context)['group_ids']
            remaining_group_ids = set(remaining_group_ids)
            for gid_tuple in add_groups_id:
                if gid_tuple[0] == 3:
                    if gid_tuple[1] in remaining_group_ids:
                        add_groups_id.remove(gid_tuple)
        for gid_tuple in add_groups_id:  # Make sure we don't remove any group that is being added
            if gid_tuple[0] == 3:
                if (4, gid_tuple[1]) in add_groups_id:
                    add_groups_id.remove(gid_tuple)
        vals['groups_id'] += add_groups_id
        return True

    def create(self, cr, user, vals, context=None):
        """
        Extends Odoo's :meth:`create()<openerp.models.Model.create>`
        to update fields ``group_ids`` and ``doctor_id``.

        :param vals: values to initialise the new record
        :type vals: dict
        :returns: id of created record
        :rtype: int
        """

        self.update_group_vals(cr, user, False, vals, context=context)
        res = super(res_users, self).create(cr, user, vals, context=dict(context or {}, mail_create_nosubscribe=True))
        if 'doctor_id' in vals:
            self.pool['nh.clinical.doctor'].write(cr, user, vals['doctor_id'], {'user_id': res}, context=context)
        if 'groups_id' in vals:
            self.update_doctor_status(cr, user, res, context=context)
        return res

    def write(self, cr, uid, ids, values, context=None):
        """
        Extends Odoo's :meth:`write()<openerp.models.Model.write>`
        method.

        :param ids: id of records to update
        :type ids: list or int
        :param values: values to update the records with
        :type values: dict
        :returns: ``True``
        :rtype: bool
        """

        if isinstance(ids, list) and len(ids) == 1:
            self.update_group_vals(cr, uid, ids[0], values, context=context)
        elif isinstance(ids, int):
            self.update_group_vals(cr, uid, ids, values, context=context)
        res = super(res_users, self).write(cr, uid, ids, values, context)
        if values.get('location_ids') or values.get('groups_id'):
            activity_pool = self.pool['nh.activity']
            activity_pool.update_users(cr, uid, ids)
        if 'groups_id' in values:
            self.update_doctor_status(cr, uid, ids, context=context)
        return res

    def name_get(self, cr, uid, ids, context=None):
        """
        Gets the names of users.

        :param ids: user ids
        :type ids: list or int
        :returns: user names
        :rtype: list
        """

        partner_pool = self.pool['res.partner']
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            doctor_groups = ['NH Clinical Doctor Group', 'NH Clinical Registrar Group',
                             'NH Clinical Consultant Group', 'NH Clinical Junior Doctor Group']
            if set(doctor_groups).intersection([g.name for g in record.groups_id]):
                name = record.title.name + ' ' + record.name if record.title else record.name
            else:
                name = record.name
            if record.parent_id and not record.is_company:
                name = "%s, %s" % (record.parent_name, name)
            if context.get('show_address_only'):
                name = partner_pool._display_address(cr, uid, record, without_company=True, context=context)
            if context.get('show_address'):
                name = name + "\n" + partner_pool._display_address(cr, uid, record, without_company=True, context=context)
            name = name.replace('\n\n','\n')
            name = name.replace('\n\n','\n')
            if context.get('show_email') and record.email:
                name = "%s <%s>" % (name, record.email)
            res.append((record.id, name))
        return res

    def update_doctor_status(self, cr, uid, ids, context=None):
        """
        Updates ``doctor`` field in :class:`res_partner` if user is a
        doctor.

        :param ids: user ids
        :type ids: list
        :returns: ``True``
        :rtype: bool
        """

        doctor_groups = ['NH Clinical Doctor Group', 'NH Clinical Registrar Group',
                         'NH Clinical Consultant Group', 'NH Clinical Junior Doctor Group']
        partner_pool = self.pool['res.partner']
        for record in self.browse(cr, uid, ids, context=context):
            if set(doctor_groups).intersection([g.name for g in record.groups_id]):
                partner_pool.write(cr, uid, record.partner_id.id, {'doctor': True}, context=context)
            elif record.partner_id.doctor:
                partner_pool.write(cr, uid, record.partner_id.id, {'doctor': False}, context=context)
        return True


class res_groups(orm.Model):
    """
    Extends Odoo's
    :class:`res_groups<openerp.addons.base.res.res_users.res_groups>`
    """

    _name = 'res.groups'
    _inherit = 'res.groups'

    def write(self, cr, uid, ids, values, context=None):
        """
        Extends Odoo's
        :meth:`write()<openerp.addons.base.res.res_users.res_groups.write>`
        to update nh_activity records with the responsible users.

        :param ids: group ids
        :type ids: list
        :param values: may contain user ids of responsible users
        :type values: dict
        :returns: ``True``
        :rtype: bool
        """

        res = super(res_groups, self).write(cr, uid, ids, values, context)
        if values.get('users'):
            activity_pool = self.pool['nh.activity']
            user_ids = []
            # iterate through groups
            for group in self.browse(cr, uid, isinstance(ids, (list, tuple)) and ids or [ids]):
                # get all users ids of users who belong to each group
                user_ids.extend([u.id for u in group.users])
            # update activities with user ids of responsible users
            activity_pool.update_users(cr, uid, user_ids)
        return res


class nh_clinical_pos(orm.Model):
    """
    Represents clinical point of service.
    """

    _name = 'nh.clinical.pos'

    _columns = {
        'name': fields.char('Point of Service', size=100, required=True, select=True),
        'code': fields.char('Code', size=256),
        'location_id': fields.many2one('nh.clinical.location', 'POS Location', required=True),
        'company_id': fields.many2one('res.company', 'Company'),
        'lot_admission_id': fields.many2one('nh.clinical.location', 'Admission Location'),
        'lot_discharge_id': fields.many2one('nh.clinical.location', 'Discharge Location'),
        }

    _sql_constraints = [('pos_code_uniq', 'unique(code)', 'The code for a location must be unique!')]


class nh_clinical_context(orm.Model):
    """
    Indicates if a specific policy is applicable to a model.

    A context will trigger actions related to the context. If an action
    is executed in a particular `context`, then its context-dependent
    actions will be triggered as a result (if there are any).
    """

    _name = 'nh.clinical.context'
    _columns = {
        'name': fields.char('Name', size=100, required=True, select=True),
        'models': fields.text('Applicable Models')
        #This should be formatted as a python list of the applicable models for the context
    }

    def check_model(self, cr, uid, ids, model, context=None):
        """
        Checks if model is applicable for the context.

        :param ids: context ids
        :type ids: list
        :param model: model to check
        :returns: ``True`` if model is applicable
        :rtype: bool
        :raises: :class:`except_orm<openerp.osv.osv.except_orm>` if not
            applicable
        """

        for c in self.browse(cr, uid, ids, context=context):
            if model not in eval(c.models):
                raise osv.except_osv('Error!', model + ' not applicable for context: %s' % c.name)
        return True


class nh_clinical_location(orm.Model):
    """
    Represents a location where a patient may be located or an activity
    may take place.

    There are different types of locations. The most common usage is to
    have a `hospital` as a parent location to a group of `wards` where
    each ward is a parent to several beds. The bed location is where the
    patient can be placed.
    """

    _name = 'nh.clinical.location'
    _types = [('poc', 'Point of Care'), ('structural', 'Structural'), ('virtual', 'Virtual'), ('pos', 'POS')]
    _usages = [('bed', 'Bed'), ('bay', 'Bay'),('ward', 'Ward'), ('room', 'Room'),('department', 'Department'), ('hospital', 'Hospital')]

    def _get_pos_id(self, cr, uid, ids, field, args, context=None):
        res = {}
        pos_pool = self.pool['nh.clinical.pos']
        for location in self.browse(cr, uid, ids, context):
            pos_location_id = self.search(cr, uid, [['parent_id', '=', False], ['child_ids', 'child_of', location.id]])
            pos_location_id = pos_location_id[0] if pos_location_id else False
            pos_id = pos_pool.search(cr, uid, [['location_id', '=', pos_location_id]])
            res[location.id] = pos_id[0] if pos_id else False
            if not pos_id:
                _logger.debug("pos_id not found for location '%s', id=%s" % (location.code, location.id))
        return res

    def _pos2location_id(self, cr, uid, ids, context=None):
        res = []
        for pos in self.browse(cr, uid, ids, context):
            res.extend(self.pool['nh.clinical.location'].search(cr, uid, [['id', 'child_of', pos.location_id.id]]))
        return res

    def _is_available(self, cr, uid, ids, field, args, context=None):
        usages = [usage[0] for usage in self._usages]
        available_location_ids = self.get_available_location_ids(
            cr, uid, usages=usages, context=context)
        res = {}
        for i in ids:
            res[i] = i in available_location_ids
        return res

    def _get_patient_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        patient_pool = self.pool['nh.clinical.patient']
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = patient_pool.search(cr, uid, [('current_location_id', 'child_of', loc.id)], context=context)
        return res

    def _get_nurse_follower_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        user_pool = self.pool['res.users']
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = user_pool.search(cr, uid, [['following_ids', 'in', [p.id for p in loc.patient_ids]],
                                                     ['groups_id.name', 'in', ['NH Clinical Nurse Group']]],
                                           context=context)
        return res

    def _get_hca_follower_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        user_pool = self.pool['res.users']
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = user_pool.search(cr, uid, [['following_ids', 'in', [p.id for p in loc.patient_ids]],
                                                     ['groups_id.name', 'in', ['NH Clinical HCA Group']]],
                                           context=context)
        return res

    def _get_user_ids(self, cr, uid, location_id, group_names=None, recursive=True, context=None):
        loc = self.browse(cr, uid, location_id, context=context)
        if not group_names:
            group_names = []
        res = []
        if recursive:
            if loc.child_ids:
                for child in loc.child_ids:
                    res += self._get_user_ids(cr, uid, child.id, group_names, context=context)
        for user in loc.user_ids:
            if not group_names:
                res += [user.id]
            elif any([g.name in group_names for g in user.groups_id]):
                res += [user.id]
        return list(set(res))

    def _get_hca_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = self._get_user_ids(cr, uid, loc.id, group_names=['NH Clinical HCA Group'], context=context)
        return res

    def _get_nurse_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = self._get_user_ids(cr, uid, loc.id, group_names=['NH Clinical Nurse Group'], context=context)
        return res

    def _get_wm_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            if loc.usage == 'ward':
                res[loc.id] = self._get_user_ids(cr, uid, loc.id, group_names=['NH Clinical Ward Manager Group'],
                                                 recursive=False, context=context)
            else:
                res[loc.id] = self._get_user_ids(cr, uid, loc.id, group_names=['NH Clinical Ward Manager Group'],
                                                 context=context)
        return res

    def _get_doctor_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = self._get_user_ids(cr, uid, loc.id,
                                             group_names=['NH Clinical Doctor Group',
                                                          'NH Clinical Junior Doctor Group',
                                                          'NH Clinical Consultant Group',
                                                          'NH Clinical Registrar Group'],
                                             context=context)
        return res

    def _get_hcas(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = len(self._get_user_ids(cr, uid, loc.id, group_names=['NH Clinical HCA Group'],
                                                 context=context))
        return res

    def _get_nurses(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = len(self._get_user_ids(cr, uid, loc.id, group_names=['NH Clinical Nurse Group'],
                                                 context=context))
        return res

    def _get_waiting_patients(self, cr, uid, ids, field, args, context=None):
        """
        Returns the number of patients waiting to be allocated into a
        location within the selected location. Which means patients that
        have open patient placement activities related to this location.
        """

        res = {}
        placement_pool = self.pool['nh.clinical.patient.placement']
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = len(placement_pool.search(cr, uid, [('suggested_location_id', '=', loc.id),
                                                              ('state', 'not in', ['completed', 'cancelled'])]))
        return res

    def _get_child_patients(self, cr, uid, ids, field, args, context=None):
        """
        Returns the number of patients related to the child locations of
        this location. Number of patients related to this location are
        not included.
        """

        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            sum = 0
            for child in loc.child_ids:
                sum += len(child.patient_ids)
            res[loc.id] = sum
        return res

    def get_closest_parent_id(self, cr, uid, location_id, usage, context=None):
        """
        Gets a location's closest ancestor (parent) location id of a
        particular usage. Returns ``False`` if no such location exists.

        :param location_id: location id
        :type location_id: int
        :param usage: usage of location.
            See :class:`nh_clinical_location`
        :returns: location id of the ancestor. Otherwise ``False``
        :rtype: int or bool
        """

        location = self.read(cr, uid, location_id, ['parent_id'], context=context)
        if not location or not location['parent_id']:
            return False
        else:
            parent = self.read(cr, uid, location['parent_id'][0], ['usage'], context=context)
        if parent['usage'] == usage:
            return parent['id']
        else:
            return self.get_closest_parent_id(cr, uid, parent['id'], usage, context=context)

    def is_child_of(self, cr, uid, location_id, code, context=None):
        """
        Checks if a location is a child of another location.

        :param location_id: location id
        :type location_id: int
        :param code: location code
        :type code: str
        :returns: the dictionary ``location_id`` (key) and a string
            containing location name and parent location name (value)
            Otherwise ``False`` is returned.
        :rtype: dict or bool
        """

        code_location_id = self.search(cr, uid, [['code', '=', code]], context=context)
        child_location_ids = self.search(cr, uid, [['id', 'child_of', code_location_id[0]]], context=context)
        return location_id in child_location_ids

    def _get_name(self, cr, uid, ids, field, args, context=None):
        result = {}
        for location in self.browse(cr, uid, ids, context=context):
            if location.usage == 'ward':
                result[location.id] = location.name
            else:
                parent_id = self.get_closest_parent_id(cr, uid, location.id, 'ward', context=context)
                if parent_id:
                    parent = self.read(cr, uid, parent_id, ['name'], context=context)
                else:
                    parent = False
                result[location.id] = '{0} [{1}]'.format(location.name, parent['name']) if parent else location.name
        return result

    def _is_available_search(self, cr, uid, obj, name, args, domain=None, context=None):
        """
        Permits searching :meth:`_is_available` method so is_available
        field is searchable, ignoring any operand not '=' or '!='
        because is_available is a boolean and thus nonsensical.
        """

        location_ids = []
        for cond in args:
            available_value = bool(cond[2])
            if cond[1] not in ['=', '!=']:
                continue
            all_ids = self.search(cr, uid, [['usage', '=', 'bed']], context=context)
            available_locations_map = self._is_available(cr, uid, all_ids, 'is_available', None, context=context)
            if cond[1] == '=':
                location_ids += [k for k, v in available_locations_map.items() if v == available_value]
            else:
                location_ids += [k for k, v in available_locations_map.items() if v != available_value]
        return [('id', 'in', location_ids)]

    _columns = {
        'name': fields.char('Location', size=100, required=True, select=True),
        'full_name': fields.function(_get_name, type='char', size=150, string='Full Name'),
        'code': fields.char('Code', size=256),
        'parent_id': fields.many2one('nh.clinical.location', 'Parent Location'),
        'child_ids': fields.one2many('nh.clinical.location', 'parent_id', 'Child Locations'),
        'type': fields.selection(_types, 'Location Type'),
        'usage': fields.selection(_usages, 'Location Usage'),
        'active': fields.boolean('Active'),
        'pos_id': fields.function(_get_pos_id, type='many2one', relation='nh.clinical.pos', string='POS', store={
            'nh.clinical.location': (lambda s, cr, uid, ids, c: s.search(cr, uid, [['id', 'child_of', ids]]), ['parent_id'], 10),
            'nh.clinical.pos': (_pos2location_id, ['location_id'], 5),
            }),
        'company_id': fields.related('pos_id', 'company_id', type='many2one', relation='res.company', string='Company'),
        'is_available': fields.function(_is_available, type='boolean', string='Is Available?', fnct_search=_is_available_search),
        'patient_capacity': fields.integer('Patient Capacity'),
        'patient_ids': fields.function(_get_patient_ids, type='many2many', relation='nh.clinical.patient', string="Patients"),
        'user_ids': fields.many2many('res.users', 'user_location_rel', 'location_id', 'user_id', 'Responsible Users'),
        # aux fields for the view, worth having a SQL model instead?
        'nurse_follower_ids': fields.function(_get_nurse_follower_ids, type='many2many', relation='res.users', string="Nurse Stand-Ins"),
        'hca_follower_ids': fields.function(_get_hca_follower_ids, type='many2many', relation='res.users', string="HCA Stand-Ins"),
        'assigned_hca_ids': fields.function(_get_hca_ids, type='many2many', relation='res.users', string="Assigned HCAs"),
        'assigned_nurse_ids': fields.function(_get_nurse_ids, type='many2many', relation='res.users', string="Assigned Nurses"),
        'assigned_wm_ids': fields.function(_get_wm_ids, type='many2many', relation='res.users', string="Assigned Ward Managers"),
        'assigned_doctor_ids': fields.function(_get_doctor_ids, type='many2many', relation='res.users', string="Assigned Doctors"),
        'related_hcas': fields.function(_get_hcas, type='integer', string="Number of related HCAs"),
        'related_nurses': fields.function(_get_nurses, type='integer', string="Number of related Nurses"),
        'waiting_patients': fields.function(_get_waiting_patients, type='integer', string="Number of Waiting Patients"),
        'child_patients': fields.function(_get_child_patients, type='integer', string="Number of Patients from child locations"),
        'context_ids': fields.many2many('nh.clinical.context', 'nh_location_context_rel', 'location_id', 'context_id', string='Related Clinical Contexts')
    }

    _defaults = {
        'active': True,
        'patient_capacity': 1
    }

    _sql_constraints = [('location_code_uniq', 'unique(code)', 'The code for a location must be unique!')]

    def get_available_location_ids(self, cr, uid, usages=None, context=None):
        """
        Gets a list of available locations, only returning beds unless
        specified otherwise.

        :param usages: location type (``ward``, ``bed``, etc.) of
            available locations
        :type usage: list
        :returns: location ids of available locations (default usage is
            ``bed``)
        :rtype: list
        """

        if not usages:
            usages = ['bed']
        activity_pool = self.pool['nh.activity']
        open_spell_ids = activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.spell'], ['state', '=', 'started']], context=context)
        busy_location_ids = [a.location_id.id if a.location_id.usage == 'bed' else False
                             for a in activity_pool.browse(cr, uid, open_spell_ids, context=context)]
        busy_location_ids = list(set(busy_location_ids))
        return self.search(cr, uid, [['usage', 'in', usages], ['id', 'not in', busy_location_ids]], context=context)

    def switch_active_status(self, cr, uid, location_id, context=None):
        """
        Activates the location if inactive and deactivates it if active.

        :param location_id: location id of location to be switched
        :type location_id: int
        :returns: ``True``
        :rtype: bool
        """

        if isinstance(location_id, list):
            location_id = location_id[0]
        location = self.browse(cr, uid, location_id, context=context)
        activity_pool = self.pool['nh.activity']
        activate_pool = self.pool['nh.clinical.location.activate']
        deactivate_pool = self.pool['nh.clinical.location.deactivate']
        if location.active:
            activity_id = deactivate_pool.create_activity(cr, SUPERUSER_ID, {}, {'location_id': location.id}, context=context)
        else:
            activity_id = activate_pool.create_activity(cr, SUPERUSER_ID, {}, {'location_id': location.id}, context=context)
        return activity_pool.complete(cr, uid, activity_id, context=context)

    def check_context_ids(self, cr, uid, context_ids, context=None):
        """

        :param cr:
        :param uid:
        :param context_ids:
        :param context:
        :return:
        """
        if isinstance(context_ids[0], list):
            if context_ids[0][0] == 4:
                context_ids = [c[1] for c in context_ids]
            elif context_ids[0][0] == 6:
                context_ids = context_ids[0][2]
            else:
                return True
        self.pool['nh.clinical.context'].check_model(cr, uid, context_ids, self._name, context=context)
        return True

    def get_by_code(self, cr, uid, code, auto_create=False, context=None):
        """
        Gets the location's id by the location's code. Creates a
        location if ``auto_create`` is ``True`` and the location doesn't
        exist.

        :param code: location's code
        :type code: str
        :param auto_create: ``False`` [default].
        :type auto_create: bool
        :returns: location id of the location. ``False`` if
            ``auto_create`` is ``True`` and location doesn't exist, the
            location id of new ward location created. Otherwise
            ``False``
        :rtype: int or bool
        """

        location_ids = self.search(cr, uid, [['code', '=', code]], context=context)
        if not location_ids:
            if not auto_create:
                return False
            else:
                _logger.warn("Location '%s' not found! Automatically creating one with this code." % code)
                user_pool = self.pool['res.users']
                user = user_pool.browse(cr, uid, uid, context=context)
                location_id = self.create(cr, uid, {
                    'name': code,
                    'code': code,
                    'pos_id': user.pos_id.id if user.pos_id else False,
                    'parent_id': user.pos_id.location_id.id if user.pos_id.location_id else False,
                    'type': 'poc',
                    'usage': 'ward'
                }, context=context)
        else:
            location_id = location_ids[0]
        return location_id

    def create(self, cr, uid, vals, context=None):
        """
        Extends Odoo's :meth:`create()<openerp.models.Model.create>`
        method. Updates :class:`nh_clinical_location` to write
        `context_ids` field.

        :param vals: values to update the records with
        :type vals: dict
        :returns: ``True``
        :rtype: bool
        """

        if vals.get('context_ids'):
            self.check_context_ids(cr, uid, vals.get('context_ids'), context=context)
        return super(nh_clinical_location, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        """
        Extends Odoo's :meth:`write()<openerp.models.Model.write>`
        method. Updates :class:`nh_clinical_location` to write
        `context_ids` field.

        :param ids: ids of the records to update
        :type ids: list
        :param vals: values to update the records with
        :type vals: dict
        :returns: ``True``
        :rtype: bool
        """

        if vals.get('context_ids'):
            self.check_context_ids(cr, uid, vals.get('context_ids'), context=context)
        return super(nh_clinical_location, self).write(cr, uid, ids, vals, context=context)


class nh_clinical_patient(osv.Model):
    """
    Represents a patient.
    """
    _name = 'nh.clinical.patient'
    _description = "A Patient"

    _inherits = {'res.partner': 'partner_id'}

    _gender = [['BOTH', 'Both'], ['F', 'Female'], ['I', 'Intermediate'],
               ['M', 'Male'], ['NSP', 'Not Specified'], ['U', 'Unknown']]
    _ethnicity = [
        ['A', 'White - British'], ['B', 'White - Irish'], ['C', 'White - Other background'],
        ['D', 'Mixed - White and Black Caribbean'], ['E', 'Mixed - White and Black African'],
        ['F', 'Mixed - White and Asian'], ['G', 'Mixed - Other background'], ['H', 'Asian - Indian'],
        ['J', 'Asian - Pakistani'], ['K', 'Asian - Bangladeshi'], ['L', 'Asian - Other background'],
        ['M', 'Black - Caribbean'], ['N', 'Black - African'], ['P', 'Black - Other background'], ['R', 'Chinese'],
        ['S', 'Other ethnic group'], ['Z', 'Not stated']
    ]

    def _get_fullname(self, vals, fmt='{fn}, {gn} {mn}'):
        """
        Formats a fullname string from family, given and middle names.

        :param vals: contains 'family_name', 'given_name' and
            'middle_names'
        :type vals: dict
        :param fmt: format for fullname. Default is
                    '{fn}, {gn}, {mn}'
        :type fmt: string
        :returns: fullname
        :rtype: string
        """

        for k in ['family_name', 'given_name', 'middle_names']:
            if k not in vals or vals[k] in [None, False]:
                vals.update({k: ''})

        return ' '.join(fmt.format(fn=vals.get('family_name'),
                                   gn=vals.get('given_name'),
                                   mn=vals.get('middle_names')).split())

    def _get_name(self, cr, uid, ids, fn, args, context=None):
        """
        Used by function field ``full_name`` to fetch the fullname for
        each patient given by patient id.

        :param ids: patient ids
        :type ids: list
        :returns: fullnames of patients
        :rtype: dict
        """

        result = dict.fromkeys(ids, False)
        for r in self.read(cr, uid, ids, ['family_name', 'given_name', 'middle_names'], context=context):
            #TODO This needs to be manipulable depending on locale
            result[r['id']] = self._get_fullname(r)
        return result

    def check_hospital_number(self, cr, uid, hospital_number, exception=False, context=None):
        """
        Checks for a patient by `hospital number`.

        :param hospital_number: patient's hospital number
        :type hospital_number: string
        :param exception: ``True`` or ``False``. Default is ``False``
        :type exception: bool
        :returns: ``True`` if patient exists. Otherwise ``False``
        :rtype: bool
        :raises: :class:`except_orm<openerp.osv.osv.except_orm>` if
            ``exception`` is ``True`` and  if the patient exists or if
            the patient does not
        """

        if not hospital_number:
            result = False
        else:
            domain = [['other_identifier', '=', hospital_number]]
            result = bool(self.search(cr, uid, domain, context=context))
        if exception:
            if result and eval(exception):
                raise osv.except_osv('Integrity Error!', 'Patient with Hospital Number %s already exists!'
                                     % hospital_number)
            elif not result and not eval(exception):
                raise osv.except_osv('Patient Not Found!', 'There is no patient with Hospital Number %s' %
                                     hospital_number)
        return result

    def check_nhs_number(self, cr, uid, nhs_number, exception=False, context=None):
        """
        Checks for patient by provided `NHS Number`.

        :param nhs_number: patient's nhs number
        :type nhs_number: string
        :param exception: ``True`` or ``False``. Default is ``False``
        :type exception: bool
        :returns: ``True`` if patient exists. Otherwise ``False``
        :rtype: bool
        :raises: :class:`except_orm<openerp.osv.osv.except_orm>` if
            ``exception`` is ``True`` and  if the patient exists or if
            the patient does not
        """

        if not nhs_number:
            result = False
        else:
            domain = [['patient_identifier', '=', nhs_number]]
            result = bool(self.search(cr, uid, domain, context=context))
        if exception:
            if result and eval(exception):
                raise osv.except_osv('Integrity Error!', 'Patient with NHS Number %s already exists!'
                                     % nhs_number)
            elif not result and not eval(exception):
                raise osv.except_osv('Patient Not Found!', 'There is no patient with NHS Number %s' %
                                     nhs_number)
        return result

    def update(self, cr, uid, identifier, data, selection='other_identifier', context=None):
        """
        Updates patient data by provided hospital number or nhs number,
        instead of patient_id as per usual.

        :param identifier: identifier of patient
        :type identifier: str
        :param data: data to write to the patient record
        :type data: dict
        :param selection: type of identifier used to lookup patient.
            Default is ``other_identifier``, which is `hospital number`.
            ``patient_identifier`` will do it through the nhs number.
        :type selection: str
        :returns: ``True``
        :rtype: bool
        """

        patient_id = self.search(cr, uid, [[selection, '=', identifier]], context=context)
        return self.write(cr, uid, patient_id, data, context=context)

    _columns = {
        'current_location_id': fields.many2one('nh.clinical.location', 'Current Location'),
        'partner_id': fields.many2one('res.partner', 'Partner', required=True, ondelete='cascade'),
        'dob': fields.datetime('Date Of Birth'),  # Partner birthdate is NOT a date.
        'sex': fields.selection(_gender, 'Sex'),
        'gender': fields.selection(_gender, 'Gender'),
        'ethnicity': fields.selection(_ethnicity, 'Ethnicity'),
        'patient_identifier': fields.char('Patient Identifier', size=100, select=True, help="NHS Number"),
        'other_identifier': fields.char('Other Identifier', size=100, select=True, help="Hospital Number"),
        'given_name': fields.char('Given Name', size=200),
        'middle_names': fields.char('Middle Name(s)', size=200),
        'family_name': fields.char('Family Name', size=200, select=True),
        'full_name': fields.function(_get_name, type='text', string="Full Name"),
        'follower_ids': fields.many2many('res.users',
                                         'user_patient_rel',
                                         'patient_id',
                                         'user_id',
                                         'Followers')
    }

    _defaults = {
        'active': True,
        'name': 'unknown',
        'gender': 'NSP',
        'ethnicity': 'Z'
    }

    def create(self, cr, uid, vals, context=None):
        """
        Extends Odoo's :meth:`create()<openerp.models.Model.create>`
        to write ``name``, ``other_identifier`` and
        ``patient_identifier`` upon creation.

        :returns: ``True`` if created
        :rtype: bool
        """

        if not vals.get('name'):
            vals.update({'name': self._get_fullname(vals)})
        if vals.get('other_identifier'):
            self.check_hospital_number(cr, uid, vals.get('other_identifier'), exception='True', context=context)
        if vals.get('patient_identifier'):
            self.check_nhs_number(cr, uid, vals.get('patient_identifier'), exception='True', context=context)
        return super(nh_clinical_patient, self).create(cr, uid, vals,
                                                       context=dict(context or {}, mail_create_nosubscribe=True))

    def write(self, cr, uid, ids, vals, context=None):
        """
        Extends Odoo's :meth:`write()<openerp.models.Model.write>`.

        :returns: ``True`` if created
        :rtype: bool
        """

        title_pool = self.pool['res.partner.title']
        if 'title' in vals.keys():
            if not isinstance(vals.get('title'), int):
                vals['title'] = title_pool.get_title_by_name(cr, uid, vals['title'], context=context)
        return super(nh_clinical_patient, self).write(cr, uid, ids, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        """
        "Deletes" a patient from the system without deleting the record
        from the database. This allows the retrieval of patient data
        if necessary.

        :param ids: ids of patients to unlink
        :type ids: list
        :returns: ``True``
        :rtype: bool
        """

        return super(nh_clinical_patient, self).write(cr, uid, ids, {'active': False}, context=context)

    def check_data(self, cr, uid, data, create=True, exception=True, context=None):
        """
        Default will check if patient exists. Either `hospital number`
        (``other_identifier``) or `NHS number` (``patient_identifier``)
        is required.

        If ``create`` is ``True``, then both ``other_identifier`` and
        ``patient_identifier`` must be unique. Otherwise either or both
        identifiers will be accepted in ``data`` parameter.

        If ``title`` is in ``data`` parameter, then method changes title
        to res.partner.title id. If ``title`` is not included, a new
        title will be created.

        :param data: must include either ``patient_identifier`` or
            ``other_identifier``
        :type data: dict
        :param create: ``True`` [default]
        :type create: bool
        :param exception: if ``True`` [default], it will raise an
            exception if no patient exists or more than one patient
            exists
        :type create: bool
        :raises: :class:`except_orm<openerp.osv.osv.except_orm>` if
            ``exception`` arguments is ``True`` and  if patient doesn't
            exists or if duplicate patients are found
        :returns: ``True`` if successful. Otherwise ``False``
        :rtype: bool
        """

        title_pool = self.pool['res.partner.title']
        if 'patient_identifier' not in data.keys() and 'other_identifier' not in data.keys():
            raise osv.except_osv('Patient Data Error!', 'Either the Hospital Number or the NHS Number is required to '
                                                        'register/update a patient.')
        if create:
            if data.get('other_identifier'):
                self.check_hospital_number(cr, uid, data['other_identifier'], exception='True', context=context)
            if data.get('patient_identifier'):
                self.check_nhs_number(cr, uid, data['patient_identifier'], exception='True', context=context)
        else:
            if data.get('other_identifier') and data.get('patient_identifier'):
                domain = ['|',
                          ['other_identifier', '=', data['other_identifier']],
                          ['patient_identifier', '=', data['patient_identifier']]]
            elif data.get('other_identifier'):
                domain = [['other_identifier', '=', data['other_identifier']]]
            else:
                domain = [['patient_identifier', '=', data['patient_identifier']]]
            patient_id = self.search(cr, uid, domain, context=context)
            if not patient_id:
                if exception:
                    raise osv.except_osv('Update Error!', 'No patient found with the provided identifier.')
                else:
                    return False
            if len(patient_id) > 1:
                if exception:
                    raise osv.except_osv('Update Error!', 'Identifiers for more than one patient provided.')
                else:
                    return False
            data['patient_id'] = patient_id[0]
        if 'title' in data.keys():
            if not isinstance(data.get('title'), int):
                data['title'] = title_pool.get_title_by_name(cr, uid, data['title'], context=context)
        return True


#FIXME: This is here to prevent mail message from complaining when creating a user
class mail_message(osv.Model):
    _name = 'mail.message'
    _inherit = 'mail.message'

    def _get_default_from(self, cr, uid, context=None):
        this = self.pool.get('res.users').browse(cr, SUPERUSER_ID, uid, context=context)
        if this.alias_name and this.alias_domain:
            return '%s <%s@%s>' % (this.name, this.alias_name, this.alias_domain)
        elif this.email:
            return '%s <%s>' % (this.name, this.email)
        else:
            return '%s <%s>' % (this.name, 'No email')


class nh_clinical_specialty(orm.Model):
    """
    Specialty represent a doctor clinical specialty
    """

    _name = 'nh.clinical.specialty'
    _description = 'A Clinical Specialty'

    _specialty_groups = [
        ['surgical', 'Surgical Specialties'], ['medical', 'Medical Specialties'], ['psychiatry', 'Psychiatry'],
        ['radiology', 'Radiology'], ['pathology', 'Pathology'], ['other', 'Other']]

    _columns = {
        'name': fields.char('Main Specialty Title', size=150),
        'code': fields.integer('Code'),
        'group': fields.selection(_specialty_groups, 'Specialty Group')
    }


class nh_clinical_doctor(orm.Model):
    """
    Represents a doctor.
    """

    _name = 'nh.clinical.doctor'
    _inherits = {'res.partner': 'partner_id'}
    _gender = [['BOTH', 'Both'], ['F', 'Female'], ['I', 'Intermediate'],
               ['M', 'Male'], ['NSP', 'Not Specified'], ['U', 'Unknown']]
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', required=1, ondelete='restrict'),
        'gender': fields.selection(_gender, 'Gender'),
        'gmc': fields.char('GMC', size=10),
        'specialty_id': fields.many2one('nh.clinical.specialty', 'Speciality'),
        'code': fields.char('Regional Code', size=10),
        'user_id': fields.many2one('res.users', 'User Account')
    }
    _defaults = {
        'gender': 'U'
    }

    def create(self, cr, user, vals, context=None):
        """
        Extends Odoo's :meth:`create()<openerp.models.Model.create>`
        to update ``doctor_id`` field in :class:`res_users`.

        :returns: ``True`` if created
        :rtype: bool
        """

        res = super(nh_clinical_doctor, self).create(cr, user, vals, context=dict(context or {}, mail_create_nosubscribe=True))
        if 'user_id' in vals:
            self.pool['res.users'].write(cr, user, vals['user_id'], {'doctor_id': res}, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        """
        Extends Odoo's :meth:`write()<openerp.models.Model.write>` to
        update ``doctor_id`` field in :class:`res_users`.

        :returns: ``True`` if created
        :rtype: bool
        """

        res = super(nh_clinical_doctor, self).write(cr, uid, ids, vals, context=context)
        if 'user_id' in vals:
            self.pool['res.users'].write(cr, uid, vals['user_id'], {'doctor_id': ids[0] if isinstance(ids, list) else ids}, context=context)
        return res

    def evaluate_doctors_dict(self, cr, uid, data, context=None):
        """
        Evaluates doctors, checking for a doctor before creating a new
        doctor if it doesn't exist.

        :param data: must contain ``doctors`` key. Its value will be a
            list of dictionaries which must contain the keys ``code``,
            ``gender``, ``gmc`` and ``type``. It many contain ``title``.
        :type data: dict
        :returns: ``True`` if either it finds a doctor or creates a new
            doctor. Otherwise ``False``
        :rtype: bool
        """

        if not data.get('doctors'):
            _logger.warn("Trying to evaluate doctors dictionary without doctors data!")
            return False
        else:
            try:
                doctors = eval(str(data['doctors']))
                patient_pool = self.pool['nh.clinical.patient']
                ref_doctor_ids = []
                con_doctor_ids = []
                for d in doctors:
                    doctor_id = self.search(cr, uid, [['code', '=', d.get('code')]], context=context)
                    if not doctor_id:
                        title_id = False
                        if 'title' in d.keys():
                            title_pool = self.pool['res.partner.title']
                            title_id = title_pool.get_title_by_name(cr, uid, d['title'], context=context)
                        doctor = {
                            'name': patient_pool._get_fullname(d),
                            'title': title_id,
                            'code': d.get('code'),
                            'gender': d.get('gender'),
                            'gmc': d.get('gmc')
                        }
                        doctor_id = self.create(cr, uid, doctor, context=context)
                    else:
                        if len(doctor_id) > 1:
                            _logger.warn("More than one doctor found with code '%s' passed id=%s" %
                                         (d.get('code'), doctor_id[0]))
                        doctor_id = doctor_id[0]
                    ref_doctor_ids.append(doctor_id) if d['type'] == 'r' else con_doctor_ids.append(doctor_id)
                ref_doctor_ids and data.update({'ref_doctor_ids': [[6, False, ref_doctor_ids]]})
                con_doctor_ids and data.update({'con_doctor_ids': [[6, False, con_doctor_ids]]})
            except:
                _logger.warn("Can't evaluate 'doctors': %s" % (data['doctors']))
                return False
        return True