from openerp.osv import orm, fields
import openerp.modules.registry as registry
import openerp
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
import logging
import pytz


_logger = logging.getLogger(__name__)

@staticmethod
def utc_timestamp(cr, uid, timestamp, context=None):
    assert isinstance(timestamp, datetime), 'Datetime instance expected'
    if context and context.get('tz'):
        tz_name = context['tz']
    else:
        reg = registry.RegistryManager.get(cr.dbname)
        tz_name = reg.get('res.users').read(cr, openerp.SUPERUSER_ID, uid, ['tz'])['tz']
    if tz_name:
        try:
            utc = pytz.timezone('UTC')
            context_tz = pytz.timezone(tz_name)
            tz_timestamp = context_tz.localize(timestamp)
            return tz_timestamp.astimezone(utc).strftime(DTF)
        except Exception:
            _logger.debug("failed to compute context/client-specific timestamp, "
                          "using the UTC value",
                          exc_info=True)
    return timestamp.strftime(DTF)

fields.datetime.utc_timestamp = utc_timestamp