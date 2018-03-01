# -*- coding: utf-8 -*-
from openerp import models, fields


class Shift(models.Model):
    _name = 'nh.clinical.shift'
    ward = fields.Many2one(comodel_name='nh.clinical.location')
    nurses = fields.Many2many(
        comodel_name='res.users', relation='shift_nurses'
    )
    hcas = fields.Many2many(
        comodel_name='res.users',
        relation='shift_hcas'
    )
