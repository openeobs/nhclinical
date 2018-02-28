# -*- coding: utf-8 -*-
from openerp import models, fields


class Shift(models.Model):
    _name = 'nh.clinical.shift'
    ward = fields.Many2one(comodel_name='nh.clinical.location')
    users_on_shift = fields.Many2many(comodel_name='res.users')
