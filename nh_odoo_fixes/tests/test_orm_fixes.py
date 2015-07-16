__author__ = 'wearp'
from datetime import datetime
import re
from openerp.osv import fields
from openerp.tests.common import TransactionCase


class TestORMFixes(TransactionCase):

    def test_utc_timestamp(self):
        cr, uid = self.cr, self.uid
        date = datetime.now()
        pattern = re.compile('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')

        timestamp = fields.datetime.utc_timestamp(cr, uid, date)
        result = re.match(pattern, timestamp)
        self.assertEquals(result.string, timestamp)