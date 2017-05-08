# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
"""
``activity.py`` defines the classes and methods to allow for an audit
event driven system to be built on top of it.
"""
import logging
from datetime import datetime
from functools import wraps

from openerp import SUPERUSER_ID, api
from openerp.osv import orm, fields, osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

_logger = logging.getLogger(__name__)


def data_model_event(callback=None):
    """
    Decorator for activity methods. This will automatically call a
    method with the same name on the
    :mod:`data model<activity.nh_activity_data>` related to the
    :mod:`activity<activity.nh_activity>` instance after calling the
    activity method. The result returned is the one from the data_model
    method.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            v8_api = False
            if isinstance(args[1], int):
                self = args[0]
                activity_id = args[1]
                v8_api = True
            else:
                self, cr, uid, activity_id = args[:4]
            if isinstance(activity_id, list) and len(activity_id) == 1:
                activity_id = activity_id[0]
            if not isinstance(activity_id, (int, long)):
                raise osv.except_osv(
                    'Type Error!',
                    "activity_id must be int or long, found to be %s" %
                    type(activity_id))
            elif activity_id < 1:
                raise osv.except_osv(
                    'ID Error!',
                    "activity_id must be > 0, found to be %s" % activity_id)
            if v8_api:
                activity = self.browse(activity_id)
            else:
                activity = self.browse(cr, uid, activity_id)
            data_model = self.pool[activity.data_model]
            if v8_api:
                func(self, self._cr, self._uid, *args[1:], **kwargs)
            else:
                func(*args, **kwargs)
            data_model_function = getattr(data_model, func.__name__)
            if v8_api:
                res = data_model_function(
                    self._cr, self._uid, *args[1:], **kwargs)
            else:
                res = data_model_function(*args[1:], **kwargs)
            return res
        return wrapper
    return decorator


class nh_activity(orm.Model):
    """
    Class representing any event that needs to be recorded by the system.

    Any user executed event that has a starting and ending point in time
    could be represented as an instance of this class.

    Most of them will need extra information recorded within them and
    that is why this class is closely related to the
    :mod:`data model<activity.nh_activity_data>` classes, which could be
    also named activity type.
    """
    _name = 'nh.activity'
    _rec_name = 'summary'
    _states = [('new', 'New'), ('scheduled', 'Scheduled'),
               ('started', 'Started'), ('completed', 'Completed'),
               ('cancelled', 'Cancelled')]
    _handlers = []

    def _get_data_type_selection(self, cr, uid, context=None):
        res = []
        for model_name, model in self.pool.models.items():
            if hasattr(model, '_description'):
                res.append((model_name, model._description))
        return res

    _columns = {
        'summary': fields.char('Summary', size=256),
        # hierarchies
        'parent_id': fields.many2one('nh.activity', 'Parent activity',
                                     readonly=True, help="Business hierarchy"),
        'child_ids': fields.one2many('nh.activity', 'parent_id',
                                     'Child Activities', readonly=True),
        'creator_id': fields.many2one('nh.activity', 'Creator activity',
                                      readonly=True,
                                      help="Evolution hierarchy"),
        'created_ids': fields.one2many('nh.activity', 'creator_id',
                                       'Created Activities', readonly=True),
        # state
        'notes': fields.text('Notes'),
        'state': fields.selection(_states, 'State', readonly=True),
        # identification
        'user_id': fields.many2one('res.users', 'Assignee', readonly=True),
        # system data
        'create_date': fields.datetime('Create Date', readonly=True),
        'write_date': fields.datetime('Write Date', readonly=True),
        'create_uid': fields.many2one('res.users', 'Created By',
                                      readonly=True),
        'write_uid': fields.many2one('res.users', 'Updated By', readonly=True),
        'terminate_uid': fields.many2one('res.users', 'Completed By',
                                         readonly=True),
        # dates planning
        'date_planned': fields.datetime('Planned Time', readonly=True),
        'date_scheduled': fields.datetime('Scheduled Time', readonly=True),
        # dates actions
        'date_started': fields.datetime('Started Time', readonly=True),
        'date_terminated': fields.datetime(
            'Termination Time', help="Completed, Aborted, Expired, Cancelled",
            readonly=True),
        # dates limits
        'date_deadline': fields.datetime('Deadline Time', readonly=True),
        'date_expiry': fields.datetime('Expiry Time', readonly=True),
        # activity type and related model/resource
        'data_model': fields.text("Data Model", required=True),
        'data_ref': fields.reference('Data Reference',
                                     _get_data_type_selection, size=256,
                                     readonly=True),
        # order
        'sequence': fields.integer("State Switch Sequence"),
        'assign_locked': fields.boolean("Assign Locked")
    }

    _sql_constraints = [('data_ref_unique', 'unique(data_ref)',
                         'Data reference must be unique!')]

    _defaults = {
        'state': 'new',
        'assign_locked': False
    }

    def create(self, cr, uid, vals, context=None):
        """
        Creates an activity. Raises an exception if ``data_model``
        isn't in parameter ``vals`` or if ``data_model`` doesn't exist
        as a table in the database.

        :param vals: must include ``data_model`` key:value pair
        :type vals: dict
        :raises: osv.except_osv
        :returns: id of created :class:`activity<nh_activity>`
        :rtype: int
        """
        if not vals.get('data_model'):
            raise osv.except_osv('Error!', "data_model is not defined!")

        data_model_pool = self.pool.get(vals['data_model'])
        if not data_model_pool:
            raise osv.except_osv(
                'Error!',
                "data_model does not exist in the model pool!"
            )
        if 'summary' not in vals:
            summary = data_model_pool.get_description()
            vals.update({'summary': summary})

        activity_id = super(nh_activity, self).create(cr, uid, vals, context)
        _logger.debug("activity '%s' created, activity.id=%s",
                      vals.get('data_model'), activity_id)
        return activity_id

    def write(self, cr, uid, ids, vals, context=None):
        """
        Writes to an activity. ``sequence`` will be updated if the
        the `state` of the activity is changed.

        :param ids: activity ids to write to
        :type ids: list
        :param vals: values to write to activity
        :type vals: dict
        :returns: ``True``
        :rtype: bool
        """
        if 'state' in vals:
            cr.execute("select coalesce(max(sequence), 0) from nh_activity")
            sequence = cr.fetchone()[0] + 1
            vals.update({'sequence': sequence})
        return super(nh_activity, self).write(cr, uid, ids, vals, context)

    def get_recursive_created_ids(self, cr, uid, activity_id, context=None):
        """
        Recursively gets ids of all activities created by an activity
        or all activitie

        :param activity_id: id of activity
        :type activity_id: int
        :return: list of activity ids
        :rtype: list
        """
        activity = self.browse(cr, uid, activity_id, context=context)
        if not activity.created_ids:
            return [activity_id]
        else:
            created_ids = [activity_id]
            for created in activity.created_ids:
                created_ids += self.get_recursive_created_ids(
                    cr, uid, created.id, context=context)
            return created_ids

    @data_model_event(callback="update_activity")
    def update_activity(self, cr, uid, activity_id, context=None):
        """
        This method is meant to refresh any real time data that needs
        to be refreshed on the activity. Does nothing as default.
        Included for potential utility on some activity types.

        :param activity_id: :mod:`activity<activity.nh_activity>` id
        :type activity_id: int
        :returns: ``True``
        :rtype: bool
        """
        return True

    @data_model_event(callback="submit")
    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Updates activity data. See
        :meth:`data model submit<activity.nh_activity_data.submit>` for
        full implementation.

        :param activity_id: :mod:`activity<activity.nh_activity>` id
        :type activity_id: int
        :param vals: dictionary containing {field_name: new_value}
        :type vals: dict
        :returns: ``True``
        :rtype: bool
        """
        if not isinstance(vals, dict):
            raise osv.except_osv('Type Error!',
                                 "vals must be a dict, found to be %s" %
                                 type(vals))
        return True

    # MGMT API
    @data_model_event(callback="schedule")
    def schedule(self, cr, uid, activity_id, date_scheduled=None,
                 context=None):
        """
        Sets ``date_scheduled`` to the specified date and changes the
        activity state to `scheduled`. See
        :meth:`data model schedule<activity.nh_activity_data.schedule>`
        for full implementation.

        :param activity_id: :mod:`activity<activity.nh_activity>` id
        :type activity_id: int
        :param date_scheduled: date formatted string
        :type date_scheduled: str
        :returns: ``True``
        :rtype: bool
        """
        if date_scheduled:
            if isinstance(date_scheduled, datetime):
                return True
            elif not isinstance(date_scheduled, str):
                raise osv.except_osv(
                    'Type Error!',
                    "date must be a datetime or a date formatted string, "
                    "found to be %s" % type(date_scheduled))
            date_format_list = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M',
                                '%Y-%m-%d %H', '%Y-%m-%d']
            res = []
            for date_format in date_format_list:
                try:
                    datetime.strptime(date_scheduled, date_format)
                except ValueError:
                    res.append(False)
                else:
                    res.append(True)
            if not any(res):
                raise osv.except_osv(
                    'Format Error!',
                    "Expected date formatted string, found %s" %
                    date_scheduled)
        return True

    @data_model_event(callback="assign")
    def assign(self, cr, uid, activity_id, user_id, context=None):
        """
        Sets ``user_id`` to the specified user if allowed by access rights.

        See :meth:`data model assign<activity.nh_activity_data.assign>`
        for full implementation.

        :param activity_id: :mod:`activity<activity.nh_activity>` id
        :type activity_id: int
        :param user_id: res.users id
        :type user_id: int
        :returns: ``True``
        :rtype: bool
        """
        if not isinstance(user_id, (int, long)):
            raise osv.except_osv(
                'Type Error!',
                "user_id must be int or long, found to be %s" % type(user_id))
        return True

    @data_model_event(callback="unassign")
    def unassign(self, cr, uid, activity_id, context=None):
        """
        Sets ``user_id`` to `False`. Only the current owner of the
        activity is allowed to do this action. See
        :meth:`data model unassign<activity.nh_activity_data.unassign>`
        for full implementation.

        :param activity_id: :mod:`activity<activity.nh_activity>` id
        :type activity_id: int
        :returns: ``True``
        :rtype: bool
        """
        return True

    @data_model_event(callback="start")
    def start(self, cr, uid, activity_id, context=None):
        """
        Sets activity ``state`` to `started`.

        See :meth:`data model start<activity.nh_activity_data.start>`
        for full implementation.

        :param activity_id: :mod:`activity<activity.nh_activity>` id
        :type activity_id: int
        :returns: ``True``
        :rtype: bool
        """
        return True

    @data_model_event(callback="complete")
    def complete(self, cr, uid, activity_id, context=None):
        """
        Sets activity ``state`` to `completed` and records the date and
        user on ``date_terminated`` and ``terminate_uid`` respectively.
        See :meth:`data model complete<activity.nh_activity_data.complete>`
        for full implementation.

        :param activity_id: :mod:`activity<activity.nh_activity>` id
        :type activity_id: int
        :returns: ``True``
        :rtype: bool
        """
        return True

    @data_model_event(callback="cancel")
    def cancel(self, cr, uid, activity_id, context=None):
        """
        Sets activity ``state`` to `cancelled` and records the date and
        user on ``date_terminated`` and ``terminate_uid`` respectively.
        See :meth:`data model cancel<activity.nh_activity_data.cancel>`
        for full implementation.

        :param activity_id: :mod:`activity<activity.nh_activity>` id
        :type activity_id: int
        :returns: ``True``
        :rtype: bool
        """
        return True


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
        return super(nh_activity_data, self).create(cr, uid, vals, context)

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
        new_activity_id = activity_pool.create(cr, uid, vals_activity, context)
        if vals_data:
            activity_pool.submit(cr, uid, new_activity_id, vals_data, context)
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
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        self.check_action(activity.state, 'start')
        activity_pool.write(
            cr, uid, activity_id,
            {'state': 'started', 'date_started': datetime.now().strftime(DTF)},
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
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        self.check_action(activity.state, 'complete')
        activity_pool.write(cr, uid, activity.id,
                            {'state': 'completed', 'terminate_uid': uid,
                             'date_terminated': datetime.now().strftime(DTF)},
                            context=context)
        _logger.debug("activity '%s', activity.id=%s completed",
                      activity.data_model, activity.id)
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
        activity = activity_pool.browse(cr, uid, activity_id, context)
        self.check_action(activity.state, 'cancel')
        activity_pool.write(cr, uid, activity_id, {
            'state': 'cancelled', 'terminate_uid': uid,
            'date_terminated': datetime.now().strftime(DTF)}, context=context)
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
            data_id = self.create(cr, uid, data_vals, context)
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
            activity = activity_pool.browse(cr, uid, active_id, context)
            activity_pool.update_activity(cr, SUPERUSER_ID, activity.id,
                                          context)
            activity_pool.complete(cr, uid, activity.id, context)
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
    def get_open_activity(self, data_model, spell_activity_id):
        """
        Get the latest open activity for the given model. The method assumes
        that only one open activity at a time is possible for the given model.
        If more than one is found an exception is raised.

        :param spell_activity_id:
        :return:
        """
        domain = [
            ('data_model', '=', data_model),
            ('state', 'not in', ['completed', 'cancelled']),
            ('parent_id', '=', spell_activity_id)
        ]
        activity_model = self.env['nh.activity']
        record = activity_model.search(domain)
        if record:
            record.ensure_one()
        return record

    @api.model
    def get_latest_activity(self, data_model, spell_activity_id):
        """
        Return the most recent activity for a given data model.

        :param data_model:
        :param spell_activity_id:
        :return:
        """
        domain = [
            ('data_model', '=', data_model),
            ('state', 'not in', ['completed', 'cancelled']),
            ('parent_id', '=', spell_activity_id)
        ]
        activity_model = self.env['nh.activity']
        recordset = activity_model.search(domain)
        if recordset:
            return recordset[-1]
        return recordset

    @api.model
    def get_open_activities_for_all_spells(self):
        """
        Get open activity(s) for all spells.
        :return: list of activities
        :rtype: list
        """
        domain = [
            ['state', 'not in', ['completed', 'cancelled']],
            ['data_model', '=', self._name]
        ]
        return self.env['nh.activity'].search(domain)
