# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
"""
Defines context.
"""
import logging

from openerp.osv import orm, fields, osv


_logger = logging.getLogger(__name__)


class nh_clinical_context(orm.Model):
    """
    Indicates if a specific policy is applicable to a model.

    A context will trigger actions related to the context. If an action
    is executed in a particular `context`, then its context-dependent
    actions will be triggered as a result (if there are any).
    """

    _name = 'nh.clinical.context'
    _columns = {
        'name': fields.char('Name', size=100, required=True, select=True),
        # formatted as a list of applicable models for the context
        'models': fields.text('Applicable Models')
    }

    def check_model(self, cr, uid, ids, model, context=None):
        """
        Checks if model is applicable for the context.

        :param ids: context ids
        :type ids: list
        :param model: model to check
        :returns: ``True`` if model is applicable
        :rtype: bool
        :raises: :class:`except_orm<openerp.osv.osv.except_orm>` if not
            applicable
        """

        for c in self.browse(cr, uid, ids, context=context):
            if model not in eval(c.models):
                raise osv.except_osv(
                    'Error!',
                    model + ' not applicable for context: %s' % c.name)
        return True
