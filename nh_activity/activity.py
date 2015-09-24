# -*- coding: utf-8 -*-
from openerp.osv import orm, fields, osv
from datetime import datetime
from openerp import SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

import logging
_logger = logging.getLogger(__name__)


def data_model_event(callback=None):
    """
    Decorator for activity methods. This will automatically call a method with the same name on the data_model related
    to the activity instance after calling the activity method. The result returned is the one from the data_model
    method.
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            self, cr, uid, activity_id = args[:4]
            if isinstance(activity_id, list) and len(activity_id) == 1:
                activity_id = activity_id[0]
            if not isinstance(activity_id, (int, long)):
                raise osv.except_osv('Type Error!', "activity_id must be int or long, found to be %s" %
                                     type(activity_id))
            elif activity_id < 1:
                raise osv.except_osv('ID Error!', "activity_id must be > 0, found to be %s" % activity_id)
            activity = self.browse(cr, uid, activity_id)
            data_model = self.pool[activity.data_model]
            f(*args, **kwargs)
            res = eval("data_model.%s(*args[1:], **kwargs)" % f.__name__)
            return res
        return wrapper
    return decorator


class nh_activity(orm.Model):
    """
    Class representing any event that needs to be recorded by the system.

    Any event that can be done by a user and has a starting and ending point could be represented as an instance of
    this class. Most of them will need extra information recorded and that is why this class is closely related to the
    activity data class, which could be also named activity type.
    """
    _name = 'nh.activity'
    _rec_name = 'summary'

    _states = [('new', 'New'), ('scheduled', 'Scheduled'),
               ('started', 'Started'), ('completed', 'Completed'), ('cancelled', 'Cancelled')]
    
    _handlers = []

    def _get_data_type_selection(self, cr, uid, context=None):
        res = [(model_name, model._description) for model_name, model in self.pool.models.items()
                           if hasattr(model, '_description')]        
        return res
    
    _columns = {
        'summary': fields.char('Summary', size=256),

        # hierarchies
        'parent_id': fields.many2one('nh.activity', 'Parent activity', readonly=True,
                                     help="Business hierarchy"),
        'child_ids': fields.one2many('nh.activity', 'parent_id', 'Child Activities', readonly=True),
        'creator_id': fields.many2one('nh.activity', 'Creator activity', readonly=True,
                                      help="Evolution hierarchy"),
        'created_ids': fields.one2many('nh.activity', 'creator_id', 'Created Activities', readonly=True),
        # state
        'notes': fields.text('Notes'),
        'state': fields.selection(_states, 'State', readonly=True),
        # identification
        'user_id': fields.many2one('res.users', 'Assignee', readonly=True),
        # system data
        'create_date': fields.datetime('Create Date', readonly=True),
        'write_date': fields.datetime('Write Date', readonly=True),
        'create_uid': fields.many2one('res.users', 'Created By', readonly=True),
        'write_uid': fields.many2one('res.users', 'Updated By', readonly=True),
        'terminate_uid': fields.many2one('res.users', 'Completed By', readonly=True),
        # dates planning
        'date_planned': fields.datetime('Planned Time', readonly=True),
        'date_scheduled': fields.datetime('Scheduled Time', readonly=True),
        #dates actions
        'date_started': fields.datetime('Started Time', readonly=True),
        'date_terminated': fields.datetime('Termination Time', help="Completed, Aborted, Expired, Cancelled", readonly=True),
        # dates limits
        'date_deadline': fields.datetime('Deadline Time', readonly=True),
        'date_expiry': fields.datetime('Expiry Time', readonly=True),
        # activity type and related model/resource
        'data_model': fields.text("Data Model", required=True),
        'data_ref': fields.reference('Data Reference', _get_data_type_selection, size=256, readonly=True),
        # order
        'sequence': fields.integer("State Switch Sequence"),
        'assign_locked': fields.boolean("Assign Locked")
    }

    # Fixing the '_sql_constraints' attribute below doesn't automatically change the database structure.
    # While creating a brand new database, no error should be risen (despite this specific case was not tested).
    # To update an existing database structure, this SQL instruction needs to be manually entered into the database:
    #
    # ALTER TABLE nh_activity ADD CONSTRAINT data_ref_unique UNIQUE (data_ref);
    #
    # (N.B: no single or double quotes are needed, but the semicolon at the end of the instruction is needed)
    #
    _sql_constraints = [('data_ref_unique', 'unique(data_ref)', 'Data reference must be unique!')]

    _defaults = {
        'state': 'new',
        'assign_locked': False
    }

    def create(self, cr, uid, vals, context=None):
        if not vals.get('data_model'):
            raise osv.except_osv('Error!', "data_model is not defined!")
        data_model_pool = self.pool.get(vals['data_model'])
        if not data_model_pool:
            raise osv.except_osv('Error!', "data_model does not exist in the model pool!")
        if 'summary' not in vals:
            vals.update({'summary': data_model_pool._description})

        activity_id = super(nh_activity, self).create(cr, uid, vals, context)
        _logger.debug("activity '%s' created, activity.id=%s" % (vals.get('data_model'), activity_id))
        return activity_id

    def write(self, cr, uid, ids, vals, context=None):
        if 'state' in vals:
            cr.execute("select coalesce(max(sequence), 0) from nh_activity")
            sequence = cr.fetchone()[0] + 1
            vals.update({'sequence': sequence})     
        return super(nh_activity, self).write(cr, uid, ids, vals, context)

    def get_recursive_created_ids(self, cr, uid, activity_id, context=None):
        """
        Recursively gets every single activity triggered by this instance or any of the ones triggered by it.
        :return: list of activity ids
        """
        activity = self.browse(cr, uid, activity_id, context=context)
        if not activity.created_ids:
            return [activity_id]
        else:
            created_ids = [activity_id]
            for created in activity.created_ids:
                created_ids += self.get_recursive_created_ids(cr, uid, created.id, context=context)
            return created_ids

    # DATA API

    @data_model_event(callback="update_activity")
    def update_activity(self, cr, uid, activity_id, context=None):
        """
        This method is meant to refresh any real time data that needs to be refreshed on the activity. Does nothing as
        default. Included for potential utility on some activity types.
        :return: True if successful
        """
        return True

    @data_model_event(callback="submit")
    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Updates data included in the vals parameter.
        :param vals: dictionary containing {field_name_to_update: new_value}
        :return: True if successful
        """
        if not isinstance(vals, dict):
            raise osv.except_osv('Type Error!', "vals must be a dict, found to be %s" % type(vals))
        return True

    # MGMT API
    @data_model_event(callback="schedule")
    def schedule(self, cr, uid, activity_id, date_scheduled=None, context=None):
        """
        Sets 'date_scheduled' to the specified date and changes the activity state to 'scheduled'.
        :return: True if successful
        """
        if date_scheduled:
            if isinstance(date_scheduled, datetime):
                return True
            elif not isinstance(date_scheduled, str):
                raise osv.except_osv('Type Error!', "date must be a datetime or a date formatted string, "
                                                    "found to be %s" % type(date_scheduled))
            date_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d %H', '%Y-%m-%d']
            res = []
            for df in date_formats:
                try:
                    datetime.strptime(date_scheduled, df)
                except ValueError:
                    res.append(False)
                else:
                    res.append(True)
            if not any(res):
                raise osv.except_osv('Format Error!', "Expected date formatted string, found %s" % date_scheduled)
        return True

    @data_model_event(callback="assign")
    def assign(self, cr, uid, activity_id, user_id, context=None):
        """
        Sets 'user_id' to the specified user if allowed by access rights.
        :param user_id: res.users id
        :return: True if successful
        """
        if not isinstance(user_id, (int, long)):
            raise osv.except_osv('Type Error!', "user_id must be int or long, found to be %s" % type(user_id))
        return True

    @data_model_event(callback="unassign")
    def unassign(self, cr, uid, activity_id, context=None):
        """
        Sets 'user_id' to False. Only the current owner of the activity is allowed to do this action.
        :return: True if successful
        """
        return True

    @data_model_event(callback="start")
    def start(self, cr, uid, activity_id, context=None):
        """
        Sets activity state to 'started'.
        :return: True if successful
        """
        return True

    @data_model_event(callback="complete")
    def complete(self, cr, uid, activity_id, context=None):
        """
        Sets activity state to 'completed' and records the date and user on 'date_terminated' and 'terminate_uid'
        respectively.
        :return: True if successful
        """
        return True

    @data_model_event(callback="cancel")
    def cancel(self, cr, uid, activity_id, context=None):
        """
        Sets activity state to 'cancelled' and records the date and user on 'date_terminated' and 'terminate_uid'
        respectively.
        :return: True if successful
        """
        return True


class nh_activity_data(orm.AbstractModel):
    _name = 'nh.activity.data'
    _transitions = {
        'new': ['schedule', 'start', 'complete', 'cancel', 'submit', 'assign', 'unassign'],
        'scheduled': ['schedule', 'start', 'complete', 'cancel', 'submit', 'assign', 'unassign'],
        'started': ['complete', 'cancel', 'submit', 'assign', 'unassign'],
        'completed': ['cancel'],
        'cancelled': []
    }
    _description = 'Undefined Activity'
    _start_view_xmlid = None
    _schedule_view_xmlid = None
    _submit_view_xmlid = None
    _complete_view_xmlid = None
    _cancel_view_xmlid = None
    _form_description = None

    def is_action_allowed(self, state, action):
        return action in self._transitions[state]

    def check_action(self, state, action):
        if not self.is_action_allowed(state, action):
            raise osv.except_osv('Transition Error!',
                                 "event '%s' on activity type '%s' can not be executed from state '%s'" %
                                 (action, self._name, state))
        return True
    
    _columns = {
        'name': fields.char('Name', size=256),
        'activity_id': fields.many2one('nh.activity', "activity"),
        'date_started': fields.related('activity_id', 'date_started', string='Start Time', type='datetime'),
        'date_terminated': fields.related('activity_id', 'date_terminated', string='Terminated Time', type='datetime'),
        'state': fields.related('activity_id', 'state', type='char', string='State', size=64),
        'terminate_uid': fields.related('activity_id', 'terminate_uid', string='Completed By', type='many2one',
                                        relation='res.users')
    }
    _order = 'id desc'
        
    def create(self, cr, uid, vals, context=None):
        return super(nh_activity_data, self).create(cr, uid, vals, context)

    def create_activity(self, cr, uid, vals_activity={}, vals_data={}, context=None):
        """
        Creates a new activity of the current data type.
        :return: created activity id.
        """
        if not isinstance(vals_activity, dict):
            raise osv.except_osv('Type Error!', 'vals_activity must be a dict, found {}'.format(type(vals_activity)))
        if not isinstance(vals_data, dict):
            raise osv.except_osv('Type Error!', 'vals_data must be a dict, found {}'.format(type(vals_data)))
        activity_pool = self.pool['nh.activity']
        vals_activity.update({'data_model': self._name})
        new_activity_id = activity_pool.create(cr, uid, vals_activity, context)
        if vals_data:
            activity_pool.submit(cr, uid, new_activity_id, vals_data, context)
        return new_activity_id

    def start(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        self.check_action(activity.state, 'start')
        activity_pool.write(cr, uid, activity_id, {'state': 'started', 'date_started': datetime.now().strftime(DTF)}, context=context)
        _logger.debug("activity '%s', activity.id=%s started" % (activity.data_model, activity.id))
        return True

    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        self.check_action(activity.state, 'complete')
        activity_pool.write(cr, uid, activity.id,
                            {'state': 'completed', 'terminate_uid': uid,
                             'date_terminated': datetime.now().strftime(DTF)}, context=context)
        _logger.debug("activity '%s', activity.id=%s completed" % (activity.data_model, activity.id))
        return True

    def assign(self, cr, uid, activity_id, user_id, context=None):
        """
        Assigns activity to a user. Raises an exception if the activity
        is already assigned to another user. If the activity is already
        assigned to the same user, then the activity is locked.
        :param activity_id:
        :param user_id:
        :return: True if successful
        """
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        self.check_action(activity.state, 'assign')
        if activity.user_id and activity.user_id.id != user_id:
            raise osv.except_osv('Error!', "activity is already assigned to '%s'" % activity.user_id.name)
        if not activity.assign_locked:
            if not activity.user_id:
                activity_pool.write(cr, uid, activity_id, {'user_id': user_id}, context=context)
                _logger.debug("activity '%s', activity.id=%s assigned to user.id=%s" % (activity.data_model,
                                                                                        activity.id, user_id))
            else:
                activity_pool.write(cr, uid, activity_id, {'assign_locked': True}, context=context)
                _logger.debug("activity '%s', activity.id=%s locked to user.id=%s!" % (activity.data_model,
                                                                                       activity.id, user_id))
        return True

    def unassign(self, cr, uid, activity_id, context=None):
        """
        Unassigns an activity. Raises an exception if activity is not
        assigned. Raised an exception if another user tries to unassign
        an activity not assigned to them.
        :param activity_id:
        :return: True if successful
        """
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        self.check_action(activity.state, 'unassign')
        if not activity.user_id:
            raise osv.except_osv('Error!', "activity is not assigned yet!")
        if uid != activity.user_id.id:
            raise osv.except_osv('Error!', "only the activity owner is allowed to unassign it!")
        if not activity.assign_locked:
            activity_pool.write(cr, uid, activity_id, {'user_id': False}, context=context)
            _logger.debug("activity '%s', activity.id=%s unassigned" % (activity.data_model, activity.id))
        else:
            _logger.debug("activity '%s', activity.id=%s cannot be unassigned (locked)" % (activity.data_model,
                                                                                           activity.id))
        return True

    def cancel(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context)
        self.check_action(activity.state, 'cancel')
        activity_pool.write(cr, uid, activity_id, {'state': 'cancelled',
                            'terminate_uid': uid, 'date_terminated': datetime.now().strftime(DTF)}, context=context)
        _logger.debug("activity '%s', activity.id=%s cancelled" % (activity.data_model, activity.id))
        return True

    def schedule(self, cr, uid, activity_id, date_scheduled=None, context=None):
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        self.check_action(activity.state, 'schedule')
        if not activity.date_scheduled and not date_scheduled:
            raise osv.except_osv('Error!', "Schedule date is neither set on activity nor passed to the method")
        date_scheduled = date_scheduled or activity.date_scheduled
        activity_pool.write(cr, uid, activity_id, {'date_scheduled': date_scheduled, 'state': 'scheduled'}, context=context)
        _logger.debug("activity '%s', activity.id=%s scheduled, date_scheduled='%s'" % (
        activity.data_model, activity.id, date_scheduled))
        return True

    def submit(self, cr, uid, activity_id, vals, context=None):
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        self.check_action(activity.state, 'submit')
        data_vals = vals.copy()
        if not activity.data_ref:
            _logger.debug(
                "activity '%s', activity.id=%s data submitted: %s" % (activity.data_model, activity.id, str(data_vals)))
            data_vals.update({'activity_id': activity_id})
            data_id = self.create(cr, uid, data_vals, context)
            activity_pool.write(cr, uid, activity_id, {'data_ref': "%s,%s" % (self._name, data_id)}, context=context)
        else:
            _logger.debug(
                "activity '%s', activity.id=%s data submitted: %s" % (activity.data_model, activity.id, str(vals)))
            self.write(cr, uid, activity.data_ref.id, vals, context=context)

        self.update_activity(cr, SUPERUSER_ID, activity_id, context=context)
        return True

    def update_activity(self, cr, uid, activity_id, context=None):
        """
            Hook for data-driven activity update
            Should be called on methods that change activity data
        """
        return True

    def submit_ui(self, cr, uid, ids, context=None):
        if context and context.get('active_id'):
            activity_pool = self.pool['nh.activity']
            activity_pool.write(cr, uid, context['active_id'], {'data_ref': "%s,%s" % (self._name, str(ids[0]))})
            activity = activity_pool.browse(cr, uid, context['active_id'], context)
            activity_pool.update_activity(cr, SUPERUSER_ID, activity.id, context)
            _logger.debug("activity '%s', activity.id=%s data submitted via UI" % (activity.data_model, activity.id))
        return {'type': 'ir.actions.act_window_close'}

    def complete_ui(self, cr, uid, ids, context=None):
        if context and context.get('active_id'):
            active_id = context['active_id']
            activity_pool = self.pool['nh.activity']
            activity_pool.write(cr, uid, active_id, {'data_ref': "%s,%s" % (self._name, str(ids[0]))})
            activity = activity_pool.browse(cr, uid, active_id, context)
            activity_pool.update_activity(cr, SUPERUSER_ID, activity.id, context)
            activity_pool.complete(cr, uid, activity.id, context)
            _logger.debug("activity '%s', activity.id=%s data completed via UI" % (activity.data_model, activity.id))
        return {'type': 'ir.actions.act_window_close'}

