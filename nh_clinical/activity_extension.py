# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
"""
Extends module :mod:`nh_activity<activity>`, introducing patients,
spells, users and locations. See also :mod:`base` module for more
information on their representative classes.
"""
import logging
from datetime import datetime as dt, timedelta as td

from openerp import SUPERUSER_ID, api
from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

_logger = logging.getLogger(__name__)


def list2sqlstr(lst):
    res = []
    lst = isinstance(lst, (list, tuple)) and lst or [lst]
    for item in lst:
        if isinstance(item, (int, long)):
            res.append("%s" % int(item))
        elif isinstance(item, basestring):
            res.append("'%s'" % item)
        elif item is None:
            res.append("0")
    return ",".join(res)


class nh_activity(orm.Model):
    """
    Extends class :class:`nh_activity<activity.nh_activity>`.
    """

    _name = 'nh.activity'
    _inherit = 'nh.activity'

    _columns = {
        'user_ids': fields.many2many(
            'res.users', 'activity_user_rel', 'activity_id', 'user_id',
            'Users', readonly=True),
        'patient_id': fields.many2one(
            'nh.clinical.patient', 'Patient', readonly=True),
        'location_id': fields.many2one(
            'nh.clinical.location', 'Location', readonly=True),
        'location_name': fields.related(
            'location_id', 'full_name', type='char', size=150,
            string='Location Name'),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS', readonly=True),
        'spell_activity_id': fields.many2one(
            'nh.activity', 'Spell Activity', readonly=True),
        'cancel_reason_id': fields.many2one(
            'nh.cancel.reason', 'Cancellation Reason'),
        'ward_manager_id': fields.many2one(
            'res.users', 'Ward Manager of the ward on Complete/Cancel')
    }

    def create(self, cr, uid, vals, context=None):
        """
        Extends Odoo's `create()` method.

        Writes ``user_ids`` for responsible users of the activities`
        location.

        :param vals: values to create record
        :type vals: doct
        :returns: :class:`nh_activity<activity.nh_activity>` id
        :rtype: int
        """
        res = super(nh_activity, self).create(cr, uid, vals, context=context)
        if vals.get('location_id'):
            user_ids = self.pool['nh.activity.data'].get_activity_user_ids(
                cr, uid, res, context=context)
            if vals.get('data_model') == 'nh.clinical.spell':
                self.update_users(cr, uid, user_ids)
            else:
                self.write(cr, uid, res, {'user_ids': [[6, False, user_ids]]})
        return res

    def write(self, cr, uid, ids, values, context=None):
        """
        Extends Odoo's `write()` method.

        Also writes ``user_ids`` for responsible users of the
        activities' location. See class
        :mod:`nh_clinical_location<base.nh_clinical_location>`.

        :param ids: :class:`nh_activity<activity.nh_activity>`
            record ids
        :type ids: list
        :param vals: values to update records (may include
            ``location_id``)
        :type vals: dict
        :returns: ``True``
        :rtype: bool
        """

        if not values:
            values = {}
        res = super(nh_activity, self).write(cr, uid, ids, values,
                                             context=context)
        if 'location_id' in values:
            location_pool = self.pool['nh.clinical.location']
            location = location_pool.read(cr, uid, values['location_id'],
                                          ['user_ids'], context=context)
            if location:
                self.write(cr, uid, ids,
                           {'user_ids': [[6, False, location['user_ids']]]},
                           context=context)
        return res

    @api.multi
    def cancel_with_reason(self, cancel_reason):
        """
        Cancel the activity add a cancel reason to it.

        :param cancel_reason: Reason for cancelling
        :return: ``True``
        :rtype: bool
        """
        self.cancel()
        self.cancel_reason_id = cancel_reason
        return True

    @api.model
    def cancel_open_activities(
            self, spell_act_id, model, cancel_reason=None):
        """
        Cancels all open activities associated with the spell_activity_id.

        :param spell_act_id: id of the spell activity
        :type spell_act_id: int
        :param model: model (type) of activity
        :type model: str
        :param cancel_reason: The reason used when cancel activities
        :type cancel_reason: nh.clinical.cancel_reason record
        :returns: ``True`` if all open activities are cancelled or if
            there are no open activities. Otherwise, ``False``
        :rtype: bool
        """

        domain = [('spell_activity_id', '=', spell_act_id),
                  ('data_model', '=', model),
                  ('state', 'not in', ['completed', 'cancelled'])]
        open_activity_ids = self.search(domain)
        if cancel_reason:
            return all(
                [
                    act.cancel_with_reason(cancel_reason)
                    for act in open_activity_ids
                ])
        return all(
            [act.cancel() for act in open_activity_ids]
        )

    def update_users(self, cr, uid, user_ids):
        """
        Updates activities with the user_ids of users responsible for
        the activities' locations.

        :param user_ids: user ids. See class
            :class:`res_users<base.res_users>`
        :type user_ids: list
        :returns: ``True``
        :rtype: bool
        """

        if not user_ids:
            return True

        where_clause = "where user_id in (%s)" % list2sqlstr(user_ids)

        sql = """
            delete from activity_user_rel {where_clause};
            insert into activity_user_rel
            select activity_id, user_id from
                (select distinct on (activity.id, ulr.user_id)
                        activity.id as activity_id,
                        ulr.user_id
                from user_location_rel ulr
                inner join res_groups_users_rel gur on ulr.user_id = gur.uid
                inner join ir_model_access access on access.group_id = gur.gid
                  and access.perm_responsibility = true
                inner join ir_model model on model.id = access.model_id
                inner join nh_activity activity
                  on model.model = activity.data_model
                  and activity.location_id = ulr.location_id
                  and activity.state not in ('completed','cancelled')
                where not exists
                  (select 1 from activity_user_rel
                    where activity_id=activity.id
                    and user_id=ulr.user_id )) pairs
            {where_clause}
        """.format(where_clause=where_clause)
        cr.execute(sql)
        self.update_spell_users(cr, uid, user_ids)

        return True

    def update_spell_users(self, cr, uid, user_ids=None):
        """
        Updates spell activities with the user_ids of users
        responsible for parent locations of spell location.

        :param user_ids: user ids. See class
            :class:`res_users<base.res_users>`
        :type user_ids: list
        :returns: ``True``
        :rtype: bool
        """

        if not user_ids:
            return True

        where_clause = "where user_id in (%s)" % list2sqlstr(user_ids)

        sql = """
            with
               recursive route(level, path, parent_id, id) as (
                       select 0, id::text, parent_id, id
                       from nh_clinical_location
                       where parent_id is null
                   union
                       select level + 1, path||','||location.id,
                        location.parent_id, location.id
                       from nh_clinical_location location
                       join route on location.parent_id = route.id
               ),
               parent_location as (
                   select
                       id as location_id,
                       ('{'||path||'}')::int[] as ids
                   from route
                   order by path
               )
           insert into activity_user_rel
           select activity_id, user_id from (
               select distinct on (activity.id, ulr.user_id)
                   activity.id as activity_id,
                   ulr.user_id
               from user_location_rel ulr
               inner join res_groups_users_rel gur on ulr.user_id = gur.uid
               inner join ir_model_access access
                on access.group_id = gur.gid
                and access.perm_responsibility = true
               inner join ir_model model
                on model.id = access.model_id
                and model.model = 'nh.clinical.spell'
               inner join parent_location
                on parent_location.ids  && array[ulr.location_id]
               inner join nh_activity activity
                on model.model = activity.data_model
                and activity.location_id = parent_location.location_id
               where not exists
                (select 1 from activity_user_rel
                where activity_id=activity.id and user_id=ulr.user_id )) pairs
           %s
        """ % where_clause

        cr.execute(sql)
        return True


class nh_activity_data(orm.AbstractModel):
    """
    Extends class :class:`nh_activity_data<activity.nh_activity_data>`.
    """

    _inherit = 'nh.activity.data'
    _transitions = {
        'new': ['schedule', 'start', 'complete', 'cancel',
                'submit', 'assign', 'unassign'],
        'scheduled': ['schedule', 'start', 'complete', 'cancel',
                      'submit', 'assign', 'unassign'],
        'started': ['complete', 'cancel', 'submit', 'assign', 'unassign'],
        'completed': ['cancel'],
        'cancelled': []
    }
    _POLICY = {'activities': []}

    def _audit_shift_coordinator(self, cr, uid, activity_id, context=None):
        """
        Writes shift_coordinator_id for ward manager responsible for the
        activity's location. If location doesn't exist or it's not
        within the ward or there's no ward assigned, then no audit
        happens.

        :param activity_id: activity id
        :type activity_id: int
        :return: ``True`` if the shift_coordinator_id is stored. Otherwise
            ``False``
        :rtype: bool
        """

        if isinstance(activity_id, list) and len(activity_id) == 1:
            activity_id = activity_id[0]
        activity_pool = self.pool['nh.activity']
        location_pool = self.pool['nh.clinical.location']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        if activity.location_id:
            if activity.location_id.usage != 'ward':
                ward_id = location_pool.get_closest_parent_id(
                    cr, uid, activity.location_id.id, 'ward', context=context)
                ward = location_pool.browse(cr, uid, ward_id, context=context)
            else:
                ward = activity.location_id
            if ward.assigned_wm_ids:
                ward_manager_id = ward.assigned_wm_ids[0].id
                activity_pool.write(cr, uid, activity_id,
                                    {'ward_manager_id': ward_manager_id},
                                    context=context)
                return True
        return False

    def complete(self, cr, uid, activity_id, context=None):
        """
        Extends :meth:`complete()<activity.nh_activity_data.complete>`
        method to audit the ward manager responsible for activity
        location.

        :param activity_id: activity id
        :type activity_id: int
        :return: ``True``
        :rtype: bool
        """

        res = super(nh_activity_data, self) \
            .complete(cr, uid, activity_id, context=context)
        self._audit_shift_coordinator(cr, uid, activity_id, context=context)
        return res

    def cancel(self, cr, uid, activity_id, context=None):
        """
        Extends :meth:`cancel()<activity.nh_activity_data.complete>`
        method to audit the ward manager responsible for activity
        location.

        :param activity_id: activity id
        :type activity_id: int
        :returns: ``True``
        :rtype: bool
        """

        res = super(nh_activity_data, self).cancel(cr, uid, activity_id,
                                                   context=context)
        self._audit_shift_coordinator(cr, uid, activity_id, context=context)
        return res

    def update_activity(self, cr, uid, activity_id, context=None):
        """
        Extends
        :meth:`update_activity()<activity.nh_activity_data.update_activity>`
        method.

        :param activity_id: activity id of updated activity
        :type activity_id: int
        :returns: ``True``
        :rtype: bool
        """

        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        activity_vals = {}
        location_id = self.get_activity_location_id(cr, uid, activity_id)
        patient_id = self.get_activity_patient_id(cr, uid, activity_id)
        pos_id = self.get_activity_pos_id(cr, uid, activity_id)

        if 'patient_id' in self._columns.keys():
            activity_vals.update({'patient_id': patient_id})

        activity_vals.update({'location_id': location_id,
                              'pos_id': pos_id})
        activity_pool.write(cr, uid, activity_id, activity_vals,
                            context=context)
        activity_ids = activity_pool.search(cr, uid, [
            ['patient_id', '=', patient_id],
            ['data_model', '=', 'nh.clinical.spell'],
            ['state', '=', 'started']], context=context)
        spell_activity_id = activity_ids[0] if activity_ids else False
        # user_ids depend on location_id, thus separate updates
        user_ids = self.get_activity_user_ids(cr, uid, activity_id,
                                              context=context)
        activity_pool.write(
            cr, uid, activity_id,
            {'user_ids': [(6, 0, user_ids)],
             'spell_activity_id': spell_activity_id}, context=context)
        _logger.debug(
            "activity '%s', activity.id=%s updated with: %s",
            activity.data_model, activity.id, activity_vals)
        return True

    def get_activity_pos_id(self, cr, uid, activity_id, context=None):
        """
        Gets activity point of service (POST) id.

        :param activity_id: activity id of updated activity
        :type activity_id: int
        :returns: POS id
        :rtype: int
        """

        pos_id = False
        patient_pool = self.pool['nh.clinical.patient']

        data_ids = self.search(cr, uid, [('activity_id', '=', activity_id)])
        data = self.browse(cr, uid, data_ids, context=context)[0]

        if 'pos_id' in self._columns.keys():
            pos_id = data.pos_id.id if data.pos_id else False
        if pos_id:
            return pos_id
        location_id = self.get_activity_location_id(cr, uid, activity_id)
        patient_id = self.get_activity_patient_id(cr, uid, activity_id)

        if not location_id:
            patient = patient_pool.browse(cr, uid, patient_id, context=context)

            if patient.current_location_id:
                location_id = patient.current_location_id.id
            else:
                location_id = False

            if location_id:
                location = self.pool['nh.clinical.location'].browse(
                    cr, uid, location_id, context)
                pos_id = location.pos_id.id if location.pos_id else False
                if pos_id:
                    return pos_id
        spell_pool = self.pool['nh.clinical.spell']
        spell_id = spell_pool.get_by_patient_id(cr, uid, patient_id,
                                                context=context)

        if spell_id:
            spell = spell_pool.browse(cr, uid, spell_id, context=context)
        else:
            spell = False

        pos_id = spell.pos_id.id if spell else False
        return pos_id

    def get_activity_location_id(self, cr, uid, activity_id, context=None):
        """
        Gets the activity's location id.

        :param activity_id: activity id
        :type activity_id: int
        :returns: location_id. See class
            :mod:`nh_clinical_location<base.nh_clinical_location>`
        :rtype: int
        """
        location_id = False
        data_ids = self.search(cr, uid, [('activity_id', '=', activity_id)])
        data = self.browse(cr, uid, data_ids, context=context)[0]

        if 'location_id' in self._columns.keys():
            location_id = data.location_id.id if data.location_id else False
        if not location_id:
            location_id = data.activity_id.patient_id.current_location_id.id
        if not location_id:
            location_id = data.activity_id.spell_activity_id and \
                data.activity_id.spell_activity_id.location_id.id or False

        if not location_id:
            if data.activity_id.parent_id:
                location_id = data.activity_id.parent_id.location_id.id
            else:
                location_id = False
        return location_id

    def get_activity_patient_id(self, cr, uid, activity_id, context=None):
        """
        Gets the activity's patient id.

        :param activity_id: activity id
        :type activity_id: int
        :returns: patient_id. See class
            :mod:`nh_clinical_patient<base.nh_clinical_patient>`
        :rtype: int
        """
        patient_id = False
        data_ids = self.search(cr, uid, [('activity_id', '=', activity_id)])
        data = self.browse(cr, uid, data_ids, context)[0]

        if 'patient_id' in self._columns.keys():
            patient_id = data.patient_id and data.patient_id.id or False
        return patient_id

    def get_activity_user_ids(self, cr, uid, activity_id, context=None):
        """
        Gets the activity's user ids.

        :param activity_id: activity id
        :type activity_id: int
        :returns: patient_id. See class :mod:`res_users<base.res_users>`
        :rtype: list
        """
        activity_pool = self.pool['nh.activity']
        cr.execute("select location_id from nh_activity where id = %s"
                   % activity_id)
        if not cr.fetchone()[0]:
            return []
        sql = """
                select
                    activity_id,
                    array_agg(user_id) as user_ids
                    from
                    (select distinct on (activity.id, ulr.user_id)
                        activity.id as activity_id,
                        ulr.user_id
                    from user_location_rel ulr
                    inner join res_groups_users_rel gur
                      on ulr.user_id = gur.uid
                    inner join ir_model_access access
                      on access.group_id = gur.gid
                      and access.perm_responsibility = true
                    inner join ir_model model on model.id = access.model_id
                    inner join nh_activity activity
                      on model.model = activity.data_model
                      and activity.location_id = ulr.location_id
                      and activity.id = {activity_id}) data
                group by activity_id
                """.format(activity_id=activity_id)
        cr.execute(sql)
        res = cr.dictfetchone()
        user_ids = list(res and set(res['user_ids']) or [])
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        follower_ids = [user.id for user in activity.patient_id.follower_ids]
        user_ids += follower_ids
        return list(set(user_ids))

    # TODO EOBS-2171 This can be removed?
    @api.model
    def check_policy_activity_context(self, activity_dict, location_id=None):
        """
        Check that the policy activity can be triggered based on the location's
        context (Normally eobs)

        :param activity_dict: Policy activity definition
        :type activity_dict: dict
        :param location_id: ID of location to check policy for
        :type location_id: int
        :return: True if can create activity for location
        :rtype: bool
        """
        location_model = self.env['nh.clinical.location']
        triggered_context = activity_dict.get('context')
        if triggered_context and location_id:
            location = location_model.browse(location_id)
            # Create a list of bools representing if the activity and location
            # contexts match. If none of them match then return False
            if not any(
                    [c.name == triggered_context for c in
                     location.context_ids]):
                return False
        return True

    @api.model
    def check_trigger_domains(self, activity, search_definitions=None):
        """
        Check if any records are returned for the supplied domains. If so then
        return False

        :param activity: nh.clinical.activity instance
        :param search_definitions: list of dicts with object (model to query)
            and domain (search query to carry out on model)

            for example:
            [
                {
                    'object': 'nh.clinical.patient',
                    'domain': [['patient_id', '=', XXX]]
                }
            ]
        :type: list(dict)
        :return: True if no records found, False is records found
        :rtype: bool
        """
        if not search_definitions:
            return False
        for search_definition in search_definitions:
            search_pool = self.env[search_definition['object']]
            search_domain = search_definition['domain'] + [
                ['parent_id', '=', activity.spell_activity_id.id]
            ]
            if search_pool.search(search_domain):
                return True
        return False

    @api.model
    def trigger_policy_cancel_others(self, spell_activity_id, trigger_model):
        """
        Cancel all open activities when triggering the policy

        :param spell_activity_id: ID of the spell's activity record. This is
            used by the cancel_
        """
        activity_model = self.env['nh.activity']
        model_data = self.env['ir.model.data']
        # Create a dict of the model names and cancel reasons so can do a
        # lookup while also leaving room to extend with other models
        reasons = {
            'nh.clinical.patient.placement': model_data.get_object(
                'nh_clinical', 'cancel_reason_placement')
        }
        activity_model.cancel_open_activities(
            spell_activity_id,
            trigger_model,
            cancel_reason=reasons.get(self._name)
        )

    def _get_policy_create_data(self, case=None):
        """
        Get the create_data dictionary for the policy

        :param case: Case that controls the logic used when getting policy
        :type case: int
        :return: Dictionary of values to use when creating a new activity
        :rtype: dict
        """
        return {}

    @staticmethod
    def trigger_policy_create_activity(source_activity, model, case=None):
        """
        Create a new activity using the data defined in the policy with the
        source activity as it's creator

        :param source_activity: Activity to use to get activity info from
        :type source_activity: nh.activity record
        :param model: Model to create activity on
        :type model: Odoo model
        :param case: Case to use when getting the data to create the new
            activity with
        """
        new_activity_data = {
            'patient_id': source_activity.patient_id.id
        }
        # Get the create data from the model instance (a subclass of this one)
        # so that models can define the data themselves
        new_activity_data.update(
            source_activity.data_ref._get_policy_create_data(case))
        return model.sudo(SUPERUSER_ID).create_activity(
            {
                'patient_id': source_activity.patient_id.id,
                'parent_id': source_activity.parent_id.id,
                'spell_activity_id': source_activity.spell_activity_id.id,
                'creator_id': source_activity.id
            },
            new_activity_data
        )

    @api.model
    def get_schedule_date(self, activity, recurring=False):
        """
        Get the time to schedule the activity at

        :param activity: Activity to get schedule date for
        :param recurring: If the schedule date needs to take into consideration
            recurrance for the activities
        :return: Date to schedule the activity for
        :rtype: datetime
        """
        if recurring:
            date_schedule = \
                self.get_recurring_activity_date_scheduled(activity)
        else:
            date_schedule = dt.now() + td(minutes=60)
        return date_schedule

    @api.model
    def trigger_policy_activity(
            self, source_activity, activity_dict, case=None):
        """
        Trigger the activity as defined in the policy dictionary

        :param source_activity: Record of the activity that's going to be used
            as the base for the new activities
        :type source_activity: nh.activity record
        :param activity_dict: Activity dictionary contains:
            - model
            - type
            - cancel_others (optional)
        :type activity_dict: dict
        :param case: Case to use when triggering policy
        :type case: int
        """
        triggered_model = self.env[activity_dict['model']]
        if activity_dict.get('cancel_others'):
            self.trigger_policy_cancel_others(
                source_activity.spell_activity_id.id,
                activity_dict['model']
            )
        triggered_activity = \
            self.trigger_policy_create_activity(
                source_activity, triggered_model, case)
        self.trigger_policy_change_state(triggered_activity, activity_dict)

    def trigger_policy_change_state(self, activity_id, policy_dict):
        """
        Change the state of the supplied activity in accordance with the
        supplied policy dict

        :param activity_id: ID of the activity to change state of
        :param policy_dict: Dictionary representing the policy to enact on the
            activity
        """
        activity_model = self.env['nh.activity']
        activity = activity_model.browse(activity_id)
        state = policy_dict.get('type')
        if state == 'start':
            activity.sudo(SUPERUSER_ID).start()
        elif state == 'complete':
            data = policy_dict.get('data')
            if data:
                activity.sudo(SUPERUSER_ID).submit(data)
            activity.sudo(SUPERUSER_ID).complete()
        else:
            recurring = state == 'recurring'
            schedule_date = self.get_schedule_date(
                activity, recurring=recurring)
            activity.sudo(SUPERUSER_ID).schedule(schedule_date)

    @api.model
    def trigger_policy(self, activity_id, location_id=None, case=False):
        """
        Triggers the list of activities in the ``_POLICY['activities']``
        list.

        :param activity_id: ID of the activity associated with the
            record
        :type activity_id: int
        :param location_id: location id [optional].
            Required for checking context
        :type location_id: int
        :param case: default ``False``. Otherwise integer related to
            risk of patient
        :type case: bool or int
        :returns: ``False`` if no spell activity otherwise ``True``
        :rtype: bool
        """
        # If no spell associated with activity then we want to just return
        # TODO: Refactor this so instead of passing over an activity ID it
        # can just load a record.
        activity_model = self.env['nh.activity']
        activity = activity_model.browse(activity_id)
        spell_activity = activity_model.search(
            [
                ['state', 'not in', ['completed', 'cancelled']],
                ['patient_id', '=', activity.patient_id.id],
                ['data_model', '=', 'nh.clinical.spell']
            ]
        )
        if not spell_activity.id:
            return False
        # Iterate through the activities in the policy dictionary
        for trigger_activity in self._POLICY.get('activities', []):
            # We only want to trigger the activities for the correct case if
            # defined (in EWS this would be the clinical risk)
            if case and trigger_activity.get('case') != case:
                continue
            # If there is a domain object on the triggered activity we need
            # to check there's no existing records
            if self.check_trigger_domains(
                    activity, trigger_activity.get('domains')):
                continue
            # Check that the policy applies to the location and trigger if it
            # does
            if self.check_policy_activity_context(
                    trigger_activity, location_id=location_id):
                self.trigger_policy_activity(activity, trigger_activity, case)
        return True

    @staticmethod
    def get_recurring_activity_date_scheduled(activity):
        """
        Recurring activities are ones that automatically create a new one when
        they are completed. It is common for EWS to be set as a recurring
        activity in a trust's policy.

        This method is called when an existing recurring activity has been
        completed and a new one has just been created. It returns the datetime
        which the newly created activity should be due by adding a 'frequency'
        to the current datetime.

        :param activity: Activity to get recurring date scheduled for
        :return: The datetime the newly triggered recurring activity should be
            due.
        :rtype: str
        """
        frequency = activity.data_ref.frequency
        date_scheduled = (dt.now() + td(minutes=frequency)).strftime(DTF)
        return date_scheduled

    def get_child_activity(self, activity_model, activity, data_model,
                           context=None):
        """
        Generator to return the child activity of the specified data model.
        The inputs use the Odoo v8 API record sets

        :param activity_model: Instance of nh.activity environment
        :param activity: Activity instance to get child of
        :param data_model: data_model child activity should be
        :param context: Odoo context
        :return: Record of child activity
        """
        next_activity = activity_model.search([
            ['data_model', '=', data_model],
            ['creator_id', '=', activity.id]
        ])
        finished_activity = activity.state in ['completed', 'cancelled']
        if not activity.data_ref.is_partial and finished_activity:
            yield activity
            raise StopIteration()
        elif not next_activity:
            yield activity
            raise StopIteration()
        else:
            yield next_activity
            self.get_child_activity(
                activity_model, next_activity.id, data_model)


class nh_clinical_activity_access(orm.Model):
    """
    Adds an additional permission type called ``perm_responsibility``
    to an activity. This defines if a particular user group can or
    cannot perform an activity.
    """

    _name = 'nh.clinical.activity.access'
    _auto = False
    _columns = {
        'user_id': fields.many2one('res.users', 'User'),
        'location_ids_text': fields.text('Location IDS Text'),
        'parent_location_ids_text': fields.text('Parent Location IDS Text'),
        'location_activity_ids_text': fields.text('Activity IDS Text'),
        'parent_location_activity_ids_text': fields.text(
            'Parent Location Activity IDS Text'),
    }

    def init(self, cr):
        cr.execute("""
            drop view if exists nh_clinical_activity_access;
            create or replace view
            nh_clinical_activity_access as(
                with
                    recursive route(level, path, parent_id, id) as (
                    select 0, id::text, parent_id, id
                    from nh_clinical_location
                    where parent_id is null
                union
                    select level + 1, path||','||location.id,
                        location.parent_id, location.id
                    from nh_clinical_location location
                    join route on location.parent_id = route.id
            ),
            location_parents as (
                select
                    id as location_id,
                    ('{'||path||'}')::int[] as ids
                from route
                order by path
            ),
            user_access as (
                select
                    u.id as user_id,
                    array_agg(access.model_id) as model_ids
                from res_users u
                inner join res_groups_users_rel gur on u.id = gur.uid
                inner join ir_model_access access
                    on access.group_id = gur.gid
                    and access.perm_responsibility = true
                group by u.id
            ),
            user_location as (
                select
                    ulr.user_id,
                    array_agg(ulr.location_id) as location_ids
                from user_location_rel ulr
                group by ulr.user_id
            ),
            user_location_parents_map as (
                select distinct
                   user_location.user_id,
                   parent_location_id
                from user_location
                inner join location_parents
                    on user_location.location_ids
                    && array[location_parents.location_id]
                inner join unnest(location_parents.ids) as parent_location_id
                    on array[parent_location_id] && location_parents.ids
            ),
            user_location_parents as (
                select
                    user_id,
                    array_agg(parent_location_id) as ids
                from user_location_parents_map
                group by user_id
            ),
            user_activity as (
                select
                    user_location.user_id,
                    array_agg(activity.id) as activity_ids
                from user_location
                inner join user_access
                    on user_location.user_id = user_access.user_id
                inner join nh_activity activity
                    on array[activity.location_id]
                    && user_location.location_ids
                inner join ir_model model on model.model = activity.data_model
                    and array[model.id] && user_access.model_ids
                group by user_location.user_id
            ),
            user_parent_location_activity as(
                select
                    user_location_parents.user_id,
                    array_agg(activity.id) as ids
                from user_location_parents
                inner join nh_activity activity
                    on array[activity.location_id] && user_location_parents.ids
                group by user_location_parents.user_id
            )
            select
                user_access.user_id as id,
                user_access.user_id,
                user_location.location_ids::text as location_ids_text,
                user_location_parents.ids::text as parent_location_ids_text,
                user_activity.activity_ids::text as location_activity_ids_text,
                user_parent_location_activity.ids::text
                    as parent_location_activity_ids_text,
                user_location.location_ids as location_ids,
                user_location_parents.ids as parent_location_ids,
                user_activity.activity_ids as location_activity_ids,
                user_parent_location_activity.ids
                    as parent_location_activity_ids
            from user_access
        inner join user_location on user_location.user_id = user_access.user_id
        inner join user_activity on user_activity.user_id = user_access.user_id
        inner join user_location_parents
            on user_location_parents.user_id = user_access.user_id
        inner join user_parent_location_activity
            on user_parent_location_activity.user_id = user_access.user_id
        ); """)
