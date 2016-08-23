# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import logging

from openerp.osv import orm, fields
from openerp import SUPERUSER_ID


_logger = logging.getLogger(__name__)


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
    _types = [('poc', 'Point of Care'), ('structural', 'Structural'),
              ('virtual', 'Virtual'), ('pos', 'POS')]
    _usages = [('bed', 'Bed'), ('bay', 'Bay'), ('ward', 'Ward'),
               ('room', 'Room'), ('department', 'Department'),
               ('hospital', 'Hospital')]

    def _get_pos_id(self, cr, uid, ids, field, args, context=None):
        res = {}
        pos_pool = self.pool['nh.clinical.pos']
        for location in self.browse(cr, uid, ids, context):
            pos_location_id = self.search(
                cr, uid, [['parent_id', '=', False],
                          ['child_ids', 'child_of', location.id]])
            pos_location_id = pos_location_id[0] if pos_location_id else False
            pos_id = pos_pool.search(cr, uid,
                                     [['location_id', '=', pos_location_id]])
            res[location.id] = pos_id[0] if pos_id else False
            if not pos_id:
                _logger.debug("pos_id not found for location '%s', id=%s" %
                              (location.code, location.id))
        return res

    def _pos2location_id(self, cr, uid, ids, context=None):
        res = []
        for pos in self.browse(cr, uid, ids, context):
            res.extend(self.pool['nh.clinical.location'].search(
                cr, uid, [['id', 'child_of', pos.location_id.id]]))
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
            res[loc.id] = patient_pool.search(
                cr, uid, [('current_location_id', 'child_of', loc.id)],
                context=context
            )
        return res

    def _get_nurse_follower_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        user_pool = self.pool['res.users']
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = user_pool.search(
                cr, uid,
                [['following_ids', 'in', [p.id for p in loc.patient_ids]],
                 ['groups_id.name', 'in', ['NH Clinical Nurse Group']]],
                context=context
            )
        return res

    def _get_hca_follower_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        user_pool = self.pool['res.users']
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = user_pool.search(
                cr, uid,
                [['following_ids', 'in', [p.id for p in loc.patient_ids]],
                 ['groups_id.name', 'in', ['NH Clinical HCA Group']]],
                context=context
            )
        return res

    def _get_user_ids(self, cr, uid, location_id, group_names=None,
                      recursive=True, context=None):
        loc = self.browse(cr, uid, location_id, context=context)
        if not group_names:
            group_names = []
        res = []
        if recursive:
            if loc.child_ids:
                for child in loc.child_ids:
                    res += self._get_user_ids(cr, uid, child.id, group_names,
                                              context=context)
        for user in loc.user_ids:
            if not group_names:
                res += [user.id]
            elif any([g.name in group_names for g in user.groups_id]):
                res += [user.id]
        return list(set(res))

    def _get_hca_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = self._get_user_ids(
                cr, uid, loc.id, group_names=['NH Clinical HCA Group'],
                context=context
            )
        return res

    def _get_nurse_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = self._get_user_ids(
                cr, uid, loc.id, group_names=['NH Clinical Nurse Group'],
                context=context
            )
        return res

    def _get_wm_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            if loc.usage == 'ward':
                res[loc.id] = self._get_user_ids(
                    cr, uid, loc.id,
                    group_names=['NH Clinical Shift Coordinator Group'],
                    recursive=False, context=context
                )
            else:
                res[loc.id] = self._get_user_ids(
                    cr, uid, loc.id,
                    group_names=['NH Clinical Shift Coordinator Group'],
                    context=context
                )
        return res

    def _get_doctor_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = self._get_user_ids(
                cr, uid, loc.id,
                group_names=[
                    'NH Clinical Doctor Group',
                    'NH Clinical Junior Doctor Group',
                    'NH Clinical Consultant Group',
                    'NH Clinical Registrar Group'
                ],
                context=context
            )
        return res

    def _get_hcas(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = len(self._get_user_ids(
                cr, uid, loc.id, group_names=['NH Clinical HCA Group'],
                context=context))
        return res

    def _get_nurses(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = len(self._get_user_ids(
                cr, uid, loc.id, group_names=['NH Clinical Nurse Group'],
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
            res[loc.id] = len(placement_pool.search(
                cr, uid, [('suggested_location_id', '=', loc.id),
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

        location = self.read(cr, uid, location_id, ['parent_id'],
                             context=context)
        if not location or not location['parent_id']:
            return False
        else:
            parent = self.read(cr, uid, location['parent_id'][0], ['usage'],
                               context=context)
        if parent['usage'] == usage:
            return parent['id']
        else:
            return self.get_closest_parent_id(cr, uid, parent['id'], usage,
                                              context=context)

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

        code_location_id = self.search(cr, uid, [['code', '=', code]],
                                       context=context)
        child_location_ids = self.search(
            cr, uid, [['id', 'child_of', code_location_id[0]]],
            context=context
        )
        return location_id in child_location_ids

    def _get_name(self, cr, uid, ids, field, args, context=None):
        result = {}
        for location in self.browse(cr, uid, ids, context=context):
            if location.usage == 'ward':
                result[location.id] = location.name
            else:
                parent_id = self.get_closest_parent_id(cr, uid, location.id,
                                                       'ward', context=context)
                if parent_id:
                    parent = self.read(cr, uid, parent_id, ['name'],
                                       context=context)
                else:
                    parent = False
                result[location.id] = '{0} [{1}]'.format(
                    location.name, parent['name']) if parent else location.name
        return result

    def _is_available_search(self, cr, uid, obj, name, args, domain=None,
                             context=None):
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
            all_ids = self.search(cr, uid, [['usage', '=', 'bed']],
                                  context=context)
            available_locations_map = self._is_available(
                cr, uid, all_ids, 'is_available', None, context=context)
            if cond[1] == '=':
                location_ids += [k for k, v in available_locations_map.items()
                                 if v == available_value]
            else:
                location_ids += [k for k, v in available_locations_map.items()
                                 if v != available_value]
        return [('id', 'in', location_ids)]

    _columns = {
        'name': fields.char('Location', size=100, required=True, select=True),
        'full_name': fields.function(_get_name, type='char', size=150,
                                     string='Full Name'),
        'code': fields.char('Code', size=256),
        'parent_id': fields.many2one('nh.clinical.location',
                                     'Parent Location'),
        'child_ids': fields.one2many('nh.clinical.location', 'parent_id',
                                     'Child Locations'),
        'type': fields.selection(_types, 'Location Type'),
        'usage': fields.selection(_usages, 'Location Usage'),
        'active': fields.boolean('Active'),
        'pos_id': fields.function(
            _get_pos_id, type='many2one', relation='nh.clinical.pos',
            string='POS', store={
                'nh.clinical.location': (
                    lambda s, cr, uid, ids, c:
                    s.search(cr, uid, [['id', 'child_of', ids]]),
                    ['parent_id'], 10),
                'nh.clinical.pos': (_pos2location_id, ['location_id'], 5),
            }),
        'company_id': fields.related('pos_id', 'company_id', type='many2one',
                                     relation='res.company', string='Company'),
        'is_available': fields.function(_is_available, type='boolean',
                                        string='Is Available?',
                                        fnct_search=_is_available_search),
        'patient_capacity': fields.integer('Patient Capacity'),
        'patient_ids': fields.function(_get_patient_ids, type='many2many',
                                       relation='nh.clinical.patient',
                                       string="Patients"),
        'user_ids': fields.many2many('res.users', 'user_location_rel',
                                     'location_id', 'user_id',
                                     'Responsible Users'),
        # aux fields for the view, worth having a SQL model instead?
        'nurse_follower_ids': fields.function(_get_nurse_follower_ids,
                                              type='many2many',
                                              relation='res.users',
                                              string="Nurse Stand-Ins"),
        'hca_follower_ids': fields.function(_get_hca_follower_ids,
                                            type='many2many',
                                            relation='res.users',
                                            string="HCA Stand-Ins"),
        'assigned_hca_ids': fields.function(_get_hca_ids, type='many2many',
                                            relation='res.users',
                                            string="Assigned HCAs"),
        'assigned_nurse_ids': fields.function(_get_nurse_ids,
                                              type='many2many',
                                              relation='res.users',
                                              string="Assigned Nurses"),
        'assigned_wm_ids': fields.function(
            _get_wm_ids,
            type='many2many',
            relation='res.users', string="Assigned Shift Coordinator"
        ),
        'assigned_doctor_ids': fields.function(_get_doctor_ids,
                                               type='many2many',
                                               relation='res.users',
                                               string="Assigned Doctors"),
        'related_hcas': fields.function(_get_hcas, type='integer',
                                        string="Number of related HCAs"),
        'related_nurses': fields.function(_get_nurses, type='integer',
                                          string="Number of related Nurses"),
        'waiting_patients': fields.function(
            _get_waiting_patients,
            type='integer',
            string="Number of Waiting Patients"
        ),
        'child_patients': fields.function(
            _get_child_patients, type='integer',
            string="Number of Patients from child locations"),
        'context_ids': fields.many2many('nh.clinical.context',
                                        'nh_location_context_rel',
                                        'location_id', 'context_id',
                                        string='Related Clinical Contexts')
    }

    def _get_default_context_ids(self, cr, uid, context=None):
        context_pool = self.pool['nh.clinical.context']
        context_ids = context_pool.search(cr, uid, [('name', '=', 'eobs')])
        return [(6, 0, context_ids)]

    _defaults = {
        'active': True,
        'patient_capacity': 1,
        'context_ids': _get_default_context_ids
    }

    _sql_constraints = [
        ('location_code_uniq',
         'unique(code)',
         'The code for a location must be unique!')
    ]

    def onchange_usage(self, cr, uid, ids, usage, context=None):
        """
        Hospital locations don't have parent locations and they are always
        Point of Service type.
        """
        if usage != 'hospital':
            return {}
        return {
            'value': {'parent_id': False, 'type': 'pos'}
        }

    def onchange_type(self, cr, uid, ids, usage, type, context=None):
        """
        Hospital locations can only be Point of Service type
        """
        if usage != 'hospital' or type == 'pos':
            return {}
        return {
            'warning': {
                'title': 'Warning',
                'message': 'Hospital locations can only be Point of Service'
            },
            'value': {
                'type': 'pos'
            }
        }

    def onchange_parent_id(self, cr, uid, ids, usage, parent_id, context=None):
        """
        Hospital locations can not have a parent location
        """
        if usage != 'hospital' or not parent_id:
            return {}
        return {
            'warning': {
                'title': 'Warning',
                'message': 'Hospital locations can not have a parent location'
            },
            'value': {
                'parent_id': False
            }
        }

    def get_available_location_ids(self, cr, uid, usages=None, context=None):
        """
        Gets a list of available locations, only returning beds unless
        specified otherwise.

        :param usages: location type (``ward``, ``bed``, etc.) of
            available locations
        :type usage: list
        :returns: location ids of available locations (default usage is
            ``bed``)i
        :rtype: list
        """

        if not usages:
            usages = ['bed']
        activity_pool = self.pool['nh.activity']
        open_spell_ids = activity_pool.search(
            cr, uid, [['data_model', '=', 'nh.clinical.spell'],
                      ['state', '=', 'started']],
            context=context)
        busy_location_ids = [a.location_id.id
                             if a.location_id.usage == 'bed' else False
                             for a in activity_pool.browse(cr, uid,
                                                           open_spell_ids,
                                                           context=context)]
        busy_location_ids = list(set(busy_location_ids))
        return self.search(cr, uid, [['usage', 'in', usages],
                                     ['id', 'not in', busy_location_ids]],
                           context=context)

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
            activity_id = deactivate_pool.create_activity(
                cr, SUPERUSER_ID, {}, {'location_id': location.id},
                context=context)
        else:
            activity_id = activate_pool.create_activity(
                cr, SUPERUSER_ID, {}, {'location_id': location.id},
                context=context)
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
        self.pool['nh.clinical.context'].check_model(cr, uid, context_ids,
                                                     self._name,
                                                     context=context)
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

        location_ids = self.search(cr, uid, [['code', '=', code]],
                                   context=context)
        if not location_ids:
            if not auto_create:
                return False
            else:
                _logger.warn("Location '%s' not found! "
                             "Automatically creating one with this code.",
                             code)
                user_pool = self.pool['res.users']
                user = user_pool.browse(cr, uid, uid, context=context)
                location_id = self.create(cr, uid, {
                    'name': code,
                    'code': code,
                    'pos_id': user.pos_id.id if user.pos_id else False,
                    'parent_id': user.pos_ids[0].location_id.id
                    if user.pos_ids[0].location_id else False,
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
            self.check_context_ids(cr, uid, vals.get('context_ids'),
                                   context=context)
        res = super(nh_clinical_location, self).create(
            cr, uid, vals, context=context)
        if vals.get('type') == 'pos' and vals.get('usage') == 'hospital':
            user_pool = self.pool['res.users']
            user = user_pool.browse(cr, uid, uid, context=context)
            if 'NH Clinical Admin Group' in [g.name for g in user.groups_id]:
                pos_pool = self.pool['nh.clinical.pos']
                pos_id = pos_pool.create(cr, uid, {
                    'name': vals.get('name'), 'location_id': res})
                user_pool.write(cr, uid, user.id, {'pos_ids': [[4, pos_id]]})
        return res

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
            self.check_context_ids(cr, uid, vals.get('context_ids'),
                                   context=context)
        return super(nh_clinical_location, self).write(cr, uid, ids, vals,
                                                       context=context)
