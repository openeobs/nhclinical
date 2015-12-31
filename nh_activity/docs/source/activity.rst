``activity``
============
.. automodule:: activity
    :members: data_model_event

``nh_activity``
---------------
.. autoclass:: nh_activity

    .. automethod:: create(cr, uid, vals, context=None)
    .. automethod:: get_recursive_created_ids(cr, uid, activity_id, context=None)
    .. automethod:: write(cr, uid, ids, vals, context=None)
    .. automethod:: update_activity(cr, uid, activity_id, context=None)
    .. automethod:: submit(cr, uid, activity_id, vals, context=None)
    .. automethod:: assign(cr, uid, activity_id, user_id, context=None)
    .. automethod:: unassign(cr, uid, activity_id, context=None)
    .. automethod:: complete(cr, uid, activity_id, context=None)
    .. automethod:: cancel(cr, uid, activity_id, context=None)
    .. automethod:: schedule(cr, uid, activity_id, date_scheduled=None, context=None)
    .. automethod:: start(cr, uid, activity_id, context=None)

``nh_activity_data``
--------------------
.. autoclass:: nh_activity_data
    :members:
