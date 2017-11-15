# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
"""
``activity.py`` defines the classes and methods to allow for an audit
event driven system to be built on top of it.
"""
import logging
from openerp import SUPERUSER_ID, api
from openerp.osv import orm, fields, osv

_logger = logging.getLogger(__name__)


class nh_activity_data(orm.AbstractModel):
    """
    Abstract class that relates to activity from which every activity
    type will inherit from.
    """
    _name = 'nh.activity.data'
    _transitions = {
        'new': ['schedule', 'start', 'complete', 'cancel', 'submit', 'assign',
                'unassign'],
        'scheduled': ['schedule', 'start', 'complete', 'cancel', 'submit',
                      'assign', 'unassign'],
        'started': ['complete', 'cancel', 'submit', 'assign', 'unassign'],
        'completed': ['cancel'],
        'cancelled': []
    }

    # Label for the observation suitable for display.
    _description = 'Undefined Activity'

    @classmethod
    def get_description(cls):
        return cls._description

    _start_view_xmlid = None
    _schedule_view_xmlid = None
    _submit_view_xmlid = None
    _complete_view_xmlid = None
    _cancel_view_xmlid = None
    _form_description = None

    def is_action_allowed(self, state, action):
        """
        Tells us if the specified action is allowed in the specified
        state.

        :param state: state of the activity where we want to execute the
            action.
        :type state: str
        :param action: action we want to execute.
        :type action: str
        :returns: ``True`` or ``False``
        :rtype: bool
        """
        return action in self._transitions[state]

    def check_action(self, state, action):
        if not self.is_action_allowed(state, action):
            raise osv.except_osv(
                'Transition Error!',
                "event '%s' on activity type '%s'"
                " can not be executed from state '%s'" %
                (action, self._name, state))
        return True

    _columns = {
        'name': fields.char('Name', size=256),
        'activity_id': fields.many2one('nh.activity', "activity"),
        'date_started': fields.related('activity_id', 'date_started',
                                       string='Start Time', type='datetime'),
        'date_terminated': fields.related('activity_id', 'date_terminated',
                                          string='Terminated Time',
                                          type='datetime'),
        'state': fields.related('activity_id', 'state', type='char',
                                string='State', size=64),
        'terminate_uid': fields.related('activity_id', 'terminate_uid',
                                        string='Completed By', type='many2one',
                                        relation='res.users')
    }
    _order = 'id desc'

    def create(self, cr, uid, vals, context=None):
        return super(nh_activity_data, self).create(
            cr, uid, vals, context=context)

    def create_activity(self, cr, uid, vals_activity=None, vals_data=None,
                        context=None):
        """
        Creates a new :mod:`activity<activity.nh_activity>` of the
        current data type.

        :param vals_activity: values to save in the
            :mod:`activity<activity.nh_activity>`
        :type vals_activity: dict
        :param vals_data: values to save in the
            :mod:`data model<activity.nh_activity_data`
        :type vals_data: dict
        :returns: :mod:`activity<activity.nh_activity>` id.
        :rtype: int
        """
        if not vals_activity:
            vals_activity = {}
        if not vals_data:
            vals_data = {}
        if not isinstance(vals_activity, dict):
            raise osv.except_osv(
                'Type Error!',
                'vals_activity must be a dict, found {}'.format(
                    type(vals_activity)
                )
            )
        if not isinstance(vals_data, dict):
            raise osv.except_osv(
                'Type Error!',
                'vals_data must be a dict, found {}'.format(
                    type(vals_data)
                )
            )
        activity_pool = self.pool['nh.activity']
        vals_activity.update({'data_model': self._name})
        new_activity_id = activity_pool.create(
            cr, uid, vals_activity, context=context)
        if vals_data:
            activity_pool.submit(
                cr, uid, new_activity_id, vals_data, context=context)
        return new_activity_id

    def start(self, cr, uid, activity_id, context=None):
        """
        Starts an activity and sets its ``date_started``.

        :param activity_id: :mod:`activity<activity.nh_activity>` id
        :type activity_id: int
        :returns: ``True``
        :rtype: bool
        """
        activity_pool = self.pool['nh.activity']
        datetime_model = self.pool['datetime_utils']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        self.check_action(activity.state, 'start')
        activity_pool.write(
            cr, uid, activity_id,
            {
                'state': 'started',
                'date_started': datetime_model.get_current_time(as_string=True)
            },
            context=context)
        _logger.debug("activity '%s', activity.id=%s started",
                      activity.data_model, activity.id)
        return True

    def complete(self, cr, uid, activity_id, context=None):
        """
        Completes an activity and sets its ``date_terminated``.

        :param activity_id: :mod:`activity<activity.nh_activity>` id
        :type activity_id: int
        :returns: ``True``
        :rtype: bool
        """
        activity_pool = self.pool['nh.activity']
        datetime_model = self.pool['datetime_utils']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        self.check_action(activity.state, 'complete')
        activity_pool.write(
            cr, uid, activity.id,
            {
                'state': 'completed',
                'terminate_uid': uid,
                'date_terminated':
                    datetime_model.get_current_time(as_string=True)
            },
            context=context)
        _logger.debug(
            "activity '%s', activity.id=%s completed",
            activity.data_model, activity.id
        )
        return True

    def assign(self, cr, uid, activity_id, user_id, context=None):
        """
        Assigns activity to a user. Raises an exception if it is already
        assigned to another user. If it is already assigned to the same
        user, then the activity is locked.

        :param activity_id: :mod:`activity<activity.nh_activity>` id
        :type activity_id: int
        :param user_id: res.users id
        :type user_id: int
        :returns: ``True``
        :rtype: bool
        """
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        self.check_action(activity.state, 'assign')
        if activity.user_id and activity.user_id.id != user_id:
            raise osv.except_osv('Error!',
                                 "activity is already assigned to '%s'" %
                                 activity.user_id.name)
        if not activity.assign_locked:
            if not activity.user_id:
                activity_pool.write(cr, uid, activity_id, {'user_id': user_id},
                                    context=context)
                _logger.debug("activity '%s', activity.id=%s "
                              "assigned to user.id=%s",
                              activity.data_model, activity.id, user_id)
            else:
                activity_pool.write(cr, uid, activity_id,
                                    {'assign_locked': True}, context=context)
                _logger.debug(
                    "activity '%s', activity.id=%s locked to user.id=%s!",
                    activity.data_model, activity.id, user_id)
        return True

    def unassign(self, cr, uid, activity_id, context=None):
        """
        Unassigns an activity. Raises an exception if it is not
        assigned. Raises an exception if another user tries to unassign
        an activity not assigned to them.

        :param activity_id: :mod:`activity<activity.nh_activity>` id
        :type activity_id: int
        :returns: ``True``
        :rtype: bool
        """
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        self.check_action(activity.state, 'unassign')
        if not activity.user_id:
            raise osv.except_osv('Error!', "activity is not assigned yet!")
        if uid != activity.user_id.id:
            raise osv.except_osv(
                'Error!', "only the activity owner is allowed to unassign it!")
        if not activity.assign_locked:
            activity_pool.write(cr, uid, activity_id, {'user_id': False},
                                context=context)
            _logger.debug("activity '%s', activity.id=%s unassigned",
                          activity.data_model, activity.id)
        else:
            _logger.debug(
                "activity '%s', activity.id=%s cannot be unassigned (locked)",
                activity.data_model, activity.id)
        return True

    def cancel(self, cr, uid, activity_id, context=None):
        """
        Cancels an activity and sets its ``date_terminated``.

        :param activity_id: :mod:`activity<activity.nh_activity>` id
        :type activity_id: int
        :returns: ``True``
        :rtype: bool
        """
        activity_pool = self.pool['nh.activity']
        datetime_model = self.pool['datetime_utils']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        self.check_action(activity.state, 'cancel')
        activity_pool.write(
            cr, uid, activity_id,
            {
                'state': 'cancelled',
                'terminate_uid': uid,
                'date_terminated':
                    datetime_model.get_current_time(as_string=True)
            },
            context=context
        )
        _logger.debug("activity '%s', activity.id=%s cancelled",
                      activity.data_model, activity.id)
        return True

    def schedule(self, cr, uid, activity_id, date_scheduled=None,
                 context=None):
        """
        Schedules an activity and sets its ``date_scheduled``.

        :param activity_id: :mod:`activity<activity.nh_activity>` id
        :type activity_id: int
        :param date_scheduled: date formatted string
        :type date_scheduled: str
        :returns: ``True``
        :rtype: bool
        """
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        self.check_action(activity.state, 'schedule')
        if not activity.date_scheduled and not date_scheduled:
            raise osv.except_osv(
                'Error!',
                "Schedule date is neither set on activity nor passed to the "
                "method")
        date_scheduled = date_scheduled or activity.date_scheduled
        activity_pool.write(cr, uid, activity_id,
                            {'date_scheduled': date_scheduled,
                             'state': 'scheduled'},
                            context=context)
        _logger.debug(
            "activity '%s', activity.id=%s scheduled, date_scheduled='%s'",
            activity.data_model, activity.id, date_scheduled)
        return True

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Updates submitted data. It creates a new instance of the data
        model if it does not exist yet.

        :param activity_id: :mod:`activity<activity.nh_activity>` id
        :type activity_id: int
        :param vals: values to update
        :type vals: dict
        :returns: ``True``
        :rtype: bool
        """
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        self.check_action(activity.state, 'submit')
        data_vals = vals.copy()
        if not activity.data_ref:
            _logger.debug(
                "activity '%s', activity.id=%s data submitted: %s",
                activity.data_model, activity.id, str(data_vals))
            data_vals.update({'activity_id': activity_id})
            data_id = self.create(cr, uid, data_vals, context=context)
            activity_pool.write(cr, uid, activity_id, {
                'data_ref': "%s,%s" % (self._name, data_id)}, context=context)
        else:
            _logger.debug(
                "activity '%s', activity.id=%s data submitted: %s",
                activity.data_model, activity.id, str(vals))
            self.write(cr, uid, activity.data_ref.id, vals, context=context)

        self.update_activity(cr, SUPERUSER_ID, activity_id, context=context)
        return True

    def update_activity(self, cr, uid, activity_id, context=None):
        """
        Hook for data-driven activity update.
        Should be called on methods that change activity data.
        """
        return True

    def submit_ui(self, cr, uid, ids, context=None):
        if context and context.get('active_id'):
            activity_pool = self.pool['nh.activity']
            activity_pool.write(
                cr, uid, context['active_id'],
                {'data_ref': "%s,%s" % (self._name, str(ids[0]))})
            activity = activity_pool.browse(cr, uid, context['active_id'],
                                            context)
            activity_pool.update_activity(cr, SUPERUSER_ID, activity.id,
                                          context)
            _logger.debug(
                "activity '%s', activity.id=%s data submitted via UI",
                activity.data_model, activity.id)
        return {'type': 'ir.actions.act_window_close'}

    def complete_ui(self, cr, uid, ids, context=None):
        if context and context.get('active_id'):
            active_id = context['active_id']
            activity_pool = self.pool['nh.activity']
            activity_pool.write(
                cr, uid, active_id,
                {'data_ref': "%s,%s" % (self._name, str(ids[0]))})
            activity = activity_pool.browse(
                cr, uid, active_id, context=context)
            activity_pool.update_activity(cr, SUPERUSER_ID, activity.id,
                                          context)
            activity_pool.complete(cr, uid, activity.id, context=context)
            _logger.debug(
                "activity '%s', activity.id=%s data completed via UI",
                activity.data_model, activity.id)
        return {'type': 'ir.actions.act_window_close'}

    def get_activity(self):
        data_ref = self.convert_record_to_data_ref()
        domain = [
            ('data_model', '=', self._name),
            ('data_ref', '=', data_ref)
        ]
        activity_model = self.env['nh.activity']
        activity = activity_model.search(domain)
        activity.ensure_one()
        return activity

    @api.multi
    def convert_record_to_data_ref(self):
        """
        Useful for getting the value for domains so you can search on
        `data_ref`.

        :return:
        :rtype: str
        """
        data_ref = '{model_name},{record_id}'.format(model_name=self._name,
                                                     record_id=self.id)
        return data_ref

    @staticmethod
    def format_many_2_many_fields(obs_list, field_names):
        for obs in obs_list:
            for field_name in field_names:
                comma_separated = ', '
                obs[field_name] = \
                    comma_separated.join(obs[field_name])

    @classmethod
    def _get_id_from_tuple(cls, a_tuple):
        """
        Extracts the id from one of the tuples commonly seen as the value of
        relational fields on models.

        :param a_tuple:
        :return:
        :rtype: int
        """
        return int(a_tuple[0])

    @api.model
    def get_open_activity(self, spell_activity_id):
        """
        Get the latest open activity for the given model. The method assumes
        that only one open activity at a time is possible for the given model.
        If more than one is found an exception is raised.

        :param data_model:
        :type data_model: str
        :param spell_activity_id:
        :type spell_activity_id: int
        :return:
        """
        domain = [
            ('data_model', '=', self._name),
            ('state', 'not in', ['completed', 'cancelled']),
            ('parent_id', '=', spell_activity_id)
        ]
        activity_model = self.env['nh.activity']
        record = activity_model.search(domain)
        if record:
            record.ensure_one()
        return record

    @api.model
    def get_latest_activity(self, spell_activity_id):
        """
        Return the most recent activity for a given data model.
        :param spell_activity_id:
        :return:
        """
        domain = [
            ('data_model', '=', self._name),
            ('state', 'not in', ['completed', 'cancelled']),
            ('parent_id', '=', spell_activity_id)
        ]
        activity_model = self.env['nh.activity']
        recordset = activity_model.search(domain)
        if recordset:
            return recordset[-1]
        return recordset

    @api.model
    def get_open_activities(self, spell_activity_id=None):
        """
        Get open activity(s) for one spell or all spells.
        :return: list of activities
        :rtype: list
        """
        domain = [
            ('state', 'not in', ['completed', 'cancelled']),
            ('data_model', '=', self._name)
        ]
        if spell_activity_id:
            domain.append(('spell_activity_id', '=', spell_activity_id))
        return self.env['nh.activity'].search(domain)
