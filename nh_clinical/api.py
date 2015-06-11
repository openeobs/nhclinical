# -*- coding: utf-8 -*-
import logging

from openerp.osv import orm
_logger = logging.getLogger(__name__)


class nh_clinical_api(orm.AbstractModel):
    _name = 'nh.clinical.api'
