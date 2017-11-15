# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
"""
``activity.py`` defines the classes and methods to allow for an audit
event driven system to be built on top of it.
"""
import logging
from datetime import datetime
from openerp import api
from openerp.osv import orm, fields, osv

_logger = logging.getLogger(__name__)


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

    def data_model_event(callback=None, *args, **kwargs):
        """
        Decorator for activity methods. This will automatically call a
        method with the same name on the
        :mod:`data model<activity.nh_activity_data>` related to the
        :mod:`activity<activity.nh_activity>` instance after calling the
        activity method. The result returned is the one from the data_model
        method.
        """

        def decorator(func, *args, **kwargs):
            @api.v7
            def wrapper(self, cr, uid, activity_id, *args, **kwargs):
                if isinstance(activity_id, (list, tuple)) \
                        and len(activity_id) == 1:
                    activity_id = activity_id[0]
                if not isinstance(activity_id, (int, long)):
                    raise osv.except_osv(
                        'Type Error!',
                        "activity_id must be int or long, found to be %s" %
                        type(activity_id))
                elif activity_id < 1:
                    raise osv.except_osv(
                        'ID Error!',
                        "activity_id must be > 0, found to be {}".format(
                            activity_id))
                activity_data = self.browse(cr, uid, activity_id)
                if not activity_data.data_model:
                    raise osv.except_osv(
                        'Data Model Error!',
                        'No data model found on activity.')
                data_model = self.pool[activity_data.data_model]
                func(self, cr, uid, activity_id, *args, **kwargs)
                data_model_function = getattr(data_model, func.__name__)
                res = data_model_function(
                    cr, uid, activity_id, *args, **kwargs)
                return res

            @api.v8
            def wrapper(self, *args, **kwargs):
                if not self.data_model:
                    raise osv.except_osv(
                        'Data Model Error!',
                        'No data model found on activity.')
                data_model = self.pool[self.data_model]
                func(self, self._cr, self._uid, self.id, *args, **kwargs)
                data_model_function = getattr(data_model, func.__name__)
                res = data_model_function(
                    self._cr, self._uid, self.id, *args, **kwargs)
                return res
            return wrapper

        return decorator

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

        activity_id = super(nh_activity, self).create(
            cr, uid, vals, context=context)
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
        return super(nh_activity, self).write(
            cr, uid, ids, vals, context=context)

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
