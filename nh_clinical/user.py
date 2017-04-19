# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
"""
Extends Odoo's res_users.
"""
import logging
import re

from openerp import SUPERUSER_ID, api
from openerp.osv import orm, fields, osv


_logger = logging.getLogger(__name__)


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
        'pos_ids': fields.many2many(
            'nh.clinical.pos', 'user_pos_rel', 'user_id', 'pos_id',
            'Points of Service'),
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
        result = bool(user.pos_ids)
        if not exception:
            return result
        else:
            if not result:
                raise osv.except_osv('Point of Service Not Defined!',
                                     'User %s has no POS defined.' % user.name)
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
            raise osv.except_osv(
                'Value Error!',
                'category_id field expecting list value, %s received' %
                type(vals.get('category_id')))
        elif not isinstance(vals.get('category_id')[0], (list, tuple)):
            raise osv.except_osv(
                'Value Error!',
                'many2many update expecting list or tuple value, %s received' %
                type(vals.get('category_id')[0]))
        add_groups_id = []
        if not vals.get('groups_id'):
            vals['groups_id'] = []
        for cat_val in vals.get('category_id'):
            if not isinstance(cat_val, (list, tuple)):
                raise osv.except_osv(
                    'Value Error!',
                    'many2many update expecting list or tuple value, '
                    '%s received' % type(vals.get('category_id')[0]))
            if cat_val[0] == 3:  # Removing categories / roles
                group_ids = category_pool.read(
                    cr, uid, cat_val[1], ['group_ids'],
                    context=context)['group_ids']
                for gid in group_ids:
                    add_groups_id.append((3, gid))
            elif cat_val[0] == 4:  # Adding categories / roles
                group_ids = category_pool.read(
                    cr, uid, cat_val[1], ['group_ids'],
                    context=context)['group_ids']
                for gid in group_ids:
                    add_groups_id.append((4, gid))
            elif cat_val[0] == 5:  # Removing all categories / roles
                add_groups_id = []
                group_ids = []
                parent_id = category_pool.search(
                    cr, uid, [['name', '=', 'System Administrator']])
                category_ids = category_pool.get_child_of_ids(
                    cr, uid, parent_id[0], context=context)
                for cid in category_ids:
                    group_ids += category_pool.read(
                        cr, uid, cid, ['group_ids'],
                        context=context)['group_ids']
                for gid in group_ids:
                    add_groups_id.append((3, gid))
                vals['groups_id'] += add_groups_id
                return True
            elif cat_val[0] == 6:  # Replacing categories / roles
                add_groups_id = []
                category_ids = cat_val[2]
                new_group_ids = []
                for cid in category_ids:
                    new_group_ids += category_pool.read(
                        cr, uid, cid, ['group_ids'],
                        context=context)['group_ids']
                old_group_ids = self.read(
                    cr, uid, user_id, ['groups_id'],
                    context=context)['groups_id'] if user_id else []
                for ogid in old_group_ids:
                    is_nhc_related = category_pool.search(
                        cr, uid, [['group_ids', 'in', [ogid]]],
                        context=context)
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
                raise osv.except_osv(
                    'Value Error!',
                    'Unexpected value for category_id field received: %s' %
                    cat_val)
        add_groups_id = list(set(add_groups_id))
        # Ensure no removal from group from a category the user still linked
        if user_id:
            old_cat_ids = set(
                self.read(cr, uid, user_id, ['category_id'],
                          context=context)['category_id']
            )
            del_cat_ids = [
                ctuple[1] for ctuple in vals.get('category_id')
                if ctuple[0] == 3
            ]
            new_cat_ids = [
                cid for cid in old_cat_ids if cid not in del_cat_ids]
            remaining_group_ids = []
            for cid in new_cat_ids:
                remaining_group_ids += category_pool.read(
                    cr, uid, cid, ['group_ids'], context=context)['group_ids']
            remaining_group_ids = set(remaining_group_ids)
            for gid_tuple in add_groups_id:
                if gid_tuple[0] == 3:
                    if gid_tuple[1] in remaining_group_ids:
                        add_groups_id.remove(gid_tuple)
        # Make sure we don't remove any group that is being added
        for gid_tuple in add_groups_id:
            if gid_tuple[0] == 3:
                if (4, gid_tuple[1]) in add_groups_id:
                    add_groups_id.remove(gid_tuple)
        vals['groups_id'] += add_groups_id
        return True

    @api.one
    @api.constrains('location_ids')
    def _check_location_ids(self):
        activity_model = self.env['nh.activity']
        locked_activities = activity_model.search([
            ['user_id', '=', self.id],
            ['location_id', 'not in', self.location_ids.ids]
        ])
        if locked_activities:
            locked_activities.write({'user_id': False})
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
        creator = self.browse(cr, user, user, context=context)
        if creator.pos_ids and not vals.get('pos_ids'):
            vals['pos_ids'] = [[6, 0, [p.id for p in creator.pos_ids]]]
        self.update_group_vals(cr, user, False, vals, context=context)
        res = super(res_users, self).create(
            cr, user, vals,
            context=dict(context or {}, mail_create_nosubscribe=True))
        if 'doctor_id' in vals:
            self.pool['nh.clinical.doctor'].write(
                cr, user, vals['doctor_id'], {'user_id': res}, context=context)
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
            doctor_groups = ['NH Clinical Doctor Group',
                             'NH Clinical Registrar Group',
                             'NH Clinical Consultant Group',
                             'NH Clinical Junior Doctor Group']
            if set(doctor_groups).intersection(
                    [g.name for g in record.groups_id]):
                if record.title:
                    name = record.title.name + ' ' + record.name
                else:
                    name = record.name
            else:
                name = record.name
            if record.parent_id and not record.is_company:
                name = "%s, %s" % (record.parent_name, name)
            if context.get('show_address_only'):
                name = partner_pool._display_address(
                    cr, uid, record, without_company=True, context=context)
            if context.get('show_address'):
                name = name + "\n" + partner_pool._display_address(
                    cr, uid, record, without_company=True, context=context)
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            if context.get('show_email') and record.email:
                name = "%s <%s>" % (name, record.email)
            res.append((record.id, name))
        return res

    @api.model
    def get_name(self, uid):
        return self.browse(uid).name

    def update_doctor_status(self, cr, uid, ids, context=None):
        """
        Updates ``doctor`` field in :class:`res_partner` if user is a
        doctor.

        :param ids: user ids
        :type ids: list
        :returns: ``True``
        :rtype: bool
        """

        doctor_groups = ['NH Clinical Doctor Group',
                         'NH Clinical Registrar Group',
                         'NH Clinical Consultant Group',
                         'NH Clinical Junior Doctor Group']
        partner_pool = self.pool['res.partner']
        for record in self.browse(cr, uid, ids, context=context):
            if set(doctor_groups).intersection(
                    [g.name for g in record.groups_id]):
                partner_pool.write(
                    cr, uid, record.partner_id.id,
                    {'doctor': True}, context=context)
            elif record.partner_id.doctor:
                partner_pool.write(
                    cr, uid, record.partner_id.id, {'doctor': False},
                    context=context)
        return True

    def get_groups_string(self, cr, uid, context=None):
        """
        :returns: list of NH Clinical user groups for UID in string format
        """
        user = self.browse(cr, uid, uid, context=context)
        return [re.sub(
            r' Group', '', re.sub(r'NH Clinical ', '', g.name)
        ) for g in user.groups_id if 'NH Clinical' in g.name and g.name !=
            'NH Clinical Base Group']


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


class nh_clinical_specialty(orm.Model):
    """
    Specialty represent a doctor clinical specialty
    """

    _name = 'nh.clinical.specialty'
    _description = 'A Clinical Specialty'

    _specialty_groups = [
        ['surgical', 'Surgical Specialties'],
        ['medical', 'Medical Specialties'], ['psychiatry', 'Psychiatry'],
        ['radiology', 'Radiology'], ['pathology', 'Pathology'],
        ['other', 'Other']]

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
        'partner_id': fields.many2one('res.partner', 'Partner', required=1,
                                      ondelete='restrict'),
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

        res = super(nh_clinical_doctor, self).create(
            cr, user, vals, context=dict(context or {},
                                         mail_create_nosubscribe=True))
        if 'user_id' in vals:
            self.pool['res.users'].write(
                cr, user, vals['user_id'], {'doctor_id': res}, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        """
        Extends Odoo's :meth:`write()<openerp.models.Model.write>` to
        update ``doctor_id`` field in :class:`res_users`.

        :returns: ``True`` if created
        :rtype: bool
        """

        res = super(nh_clinical_doctor, self).write(
            cr, uid, ids, vals, context=context)
        if 'user_id' in vals:
            self.pool['res.users'].write(
                cr, uid, vals['user_id'],
                {'doctor_id': ids[0] if isinstance(ids, list) else ids},
                context=context)
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
            _logger.warn("Trying to evaluate doctors dictionary without "
                         "doctors data!")
            return False
        else:
            try:
                doctors = eval(str(data['doctors']))
                patient_pool = self.pool['nh.clinical.patient']
                ref_doctor_ids = []
                con_doctor_ids = []
                for d in doctors:
                    doctor_id = self.search(
                        cr, uid, [['code', '=', d.get('code')]],
                        context=context)
                    if not doctor_id:
                        title_id = False
                        if 'title' in d.keys():
                            title_pool = self.pool['res.partner.title']
                            title_id = title_pool.get_title_by_name(
                                cr, uid, d['title'], context=context)
                        doctor = {
                            'name': patient_pool._get_fullname(d),
                            'title': title_id,
                            'code': d.get('code'),
                            'gender': d.get('gender'),
                            'gmc': d.get('gmc')
                        }
                        doctor_id = self.create(
                            cr, uid, doctor, context=context)
                    else:
                        if len(doctor_id) > 1:
                            _logger.warn("More than one doctor found with "
                                         "code '%s' passed id=%s" %
                                         (d.get('code'), doctor_id[0]))
                        doctor_id = doctor_id[0]
                    if d['type'] == 'r':
                        ref_doctor_ids.append(doctor_id)
                    else:
                        con_doctor_ids.append(doctor_id)
                ref_doctor_ids and data.update(
                    {'ref_doctor_ids': [[6, False, ref_doctor_ids]]})
                con_doctor_ids and data.update(
                    {'con_doctor_ids': [[6, False, con_doctor_ids]]})
            except:
                _logger.warn("Can't evaluate 'doctors': %s" %
                             (data['doctors']))
                return False
        return True


# FIXME: Here to prevent mail message from complaining when creating a user
class mail_message(osv.Model):
    _name = 'mail.message'
    _inherit = 'mail.message'

    def _get_default_from(self, cr, uid, context=None):
        this = self.pool.get('res.users').browse(
            cr, SUPERUSER_ID, uid, context=context)
        if this.alias_name and this.alias_domain:
            return '%s <%s@%s>' % (
                this.name, this.alias_name, this.alias_domain)
        elif this.email:
            return '%s <%s>' % (this.name, this.email)
        else:
            return '%s <%s>' % (this.name, 'No email')
