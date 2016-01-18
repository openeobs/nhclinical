# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
"""
Extends Odoo's ``res_groups`` and ``ir_model_access``.
"""
import logging

from openerp.osv import orm, fields


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
        'perm_responsibility': fields.boolean(
            'NH Clinical Activity Responsibility'),
        }


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
            for group in self.browse(
                    cr, uid, isinstance(ids, (list, tuple)) and ids or [ids]):
                # get all users ids of users who belong to each group
                user_ids.extend([u.id for u in group.users])
            # update activities with user ids of responsible users
            activity_pool.update_users(cr, uid, user_ids)
        return res
