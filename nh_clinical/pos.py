# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
"""
Defines POS class and extends Odoo's res_company.
"""
import logging

from openerp.osv import orm, fields


_logger = logging.getLogger(__name__)


class nh_clinical_pos(orm.Model):
    """
    Represents clinical point of service.
    """

    _name = 'nh.clinical.pos'

    _columns = {
        'name': fields.char('Point of Service', size=100, required=True,
                            select=True),
        'code': fields.char('Code', size=256),
        'location_id': fields.many2one('nh.clinical.location', 'POS Location',
                                       required=True),
        'company_id': fields.many2one('res.company', 'Company'),
        'lot_admission_id': fields.many2one('nh.clinical.location',
                                            'Admission Location'),
        'lot_discharge_id': fields.many2one('nh.clinical.location',
                                            'Discharge Location'),
        }

    _sql_constraints = [
        ('pos_code_uniq', 'unique(code)',
         'The code for a location must be unique!')
    ]


class res_company(orm.Model):
    """
    Extends Odoo's
    :class:`res_company<openerp.addons.base.res.res_company.res_company>`
    to include one-to-many point of service (pos) field. See
    :class:`nh_clinical_pos`.
    """

    _name = 'res.company'
    _inherit = 'res.company'
    _columns = {
        'pos_ids': fields.one2many('nh.clinical.pos', 'company_id',
                                   'Points of Service'),
    }
