# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import logging
from datetime import datetime

import openerp
import openerp.modules.registry as registry
import pytz
from openerp.osv import fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from pytz.exceptions import UnknownTimeZoneError, NonExistentTimeError

_logger = logging.getLogger(__name__)


@staticmethod
def utc_timestamp(cr, uid, timestamp, context=None):
    assert isinstance(timestamp, datetime), 'Datetime instance expected'
    if context and context.get('tz'):
        tz_name = context['tz']
    else:
        reg = registry.RegistryManager.get(cr.dbname)
        tz_name = reg.get('res.users').read(
            cr, openerp.SUPERUSER_ID, uid, ['tz'])['tz']

    if tz_name:
        try:
            utc = pytz.timezone('UTC')
            context_tz = pytz.timezone(tz_name)
            tz_timestamp = context_tz.localize(timestamp)
        except (UnknownTimeZoneError, NonExistentTimeError):
            _logger.debug("Failed to compute context/client-specific timestamp"
                          "Using the UTC value.", exc_info=True)
        else:
            return tz_timestamp.astimezone(utc).strftime(DTF)

    return timestamp.strftime(DTF)


fields.datetime.utc_timestamp = utc_timestamp
