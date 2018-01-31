from openerp.osv import orm, fields


class NhCancelReason(orm.Model):
    """
    Cancellation reason for an activity.
    """

    _name = 'nh.cancel.reason'
    _columns = {
        'name': fields.char('Name', size=300),
        'system': fields.boolean('System/User Reason')
    }
