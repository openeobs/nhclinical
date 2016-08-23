# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
"""
``partner.py`` extends Odoo classes for doctor and role
functionality.
"""
import logging

from openerp.osv import orm, fields


_logger = logging.getLogger(__name__)


# Must precede res_company otherwise new columns will not be located
class res_partner(orm.Model):
    """
    Extends Odoo's `res_partner` which defines a business entity i.e.
    customer, supplier, employer.

    Extension adds boolean field ``doctor`` and ``code`` for doctor
    type.

    Please note: must precede :class:`res_company` (below) to ensure
    these fields are added to the model in the database.
    """

    _inherit = 'res.partner'
    _columns = {
        'doctor': fields.boolean(
            'Doctor', help="Check this box if this contact is a Doctor"),
        'code': fields.char('Code', size=256),
    }
    _defaults = {
        'notify_email': lambda *args: 'none'
    }

    def create(self, cr, user, vals, context=None):
        """
        Extends Odoo's `create()` to update fields ``group_ids`` and
        ``doctor_id``.
        """

        return super(res_partner, self).create(
            cr, user, vals,
            context=dict(context or {}, mail_create_nosubscribe=True)
        )


class res_partner_category_extension(orm.Model):
    """
    Extends Odoo's `res_partner_category` to add functionality for
    roles.

    Creates many-to-many relationship between categories (roles) and
    groups, allowing a relation between each role and corresponding
    group(s).

    An example would be the role 'Registrar' belonging to groups base,
    doctor, senior doctor and registrar groups.
    """

    _inherit = 'res.partner.category'
    _columns = {
        'group_ids': fields.many2many(
            'res.groups', 'category_group_rel', 'category_id', 'group_id',
            'Related Groups'),
    }

    def name_get(self, cr, user, ids, context=None):
        """
        Extends Odoo's `name_get()` method, fetching the short version
        of category name belonging to ids (without their direct
        parent).

        :param user: user id
        :type user: int
        :param ids: ids of the categories
        :type ids: list
        :return: categories' display names
        :rtype: list
        """

        if context:
            ctx = context.copy()
        else:
            ctx = {}
        ctx['partner_category_display'] = 'short'
        return super(res_partner_category_extension, self).name_get(
            cr, user, ids, context=ctx)

    def get_child_of_ids(self, cr, uid, id, context=None):
        """
        Gets all child category ids of parent, recursively.

        :param id: parent id
        :type id: int
        :returns: parent id follow by child ids
        :rtype: list
        """
        res = [id]
        child_ids = self.read(
            cr, uid, id, ['child_ids'], context=context)['child_ids']
        if not child_ids:
            return res
        else:
            for c in child_ids:
                res += self.get_child_of_ids(cr, uid, c, context=context)
            return res

    def get_user_roles(self, cr, uid):
        partner_category_model = self.pool['res.partner.category']
        all_partner_category_ids = partner_category_model.search(cr, uid, [])
        partner_category_model.read(cr, uid, all_partner_category_ids)


class res_partner_title_extension(orm.Model):
    """
    Extends Odoo's `res_partner_title` to include method
    ``get_title_by_name()``.
    """

    _inherit = 'res.partner.title'

    def get_title_by_name(self, cr, uid, title, create=True, context=None):
        """
        Searches for the title by name. If the title does not exist,
        a new title is created by default.

        :param title: title of partner ('Mr', 'Dr, 'Miss', etc.)
        :type title: string
        :param create: when ``True``, the title will be created if the
            title doesn't exist
        :type create: ``bool`` [default is ``True``]
        :returns: id of title
        :rtype: int
        """

        title = title.replace('.', '').replace(' ', '').lower()
        title_id = self.search(cr, uid, [['name', '=', title]],
                               context=context)
        if not create:
            return title_id[0] if title_id else False
        else:
            if not title_id:
                return self.create(cr, uid, {'name': title}, context=context)
            else:
                return title_id[0]
