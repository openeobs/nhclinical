# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import re

from datetime import datetime
from mock import patch
from openerp.osv import fields
from openerp.tests.common import TransactionCase


class TestORMFixes(TransactionCase):

    @classmethod
    def setUpClass(cls):
        cls.pattern = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
        cls.date = datetime.now()
        cls.context = {'tz': 'GB'}

    def test_01_utc_timestamp(self):
        cr, uid = self.cr, self.uid

        timestamp = fields.datetime.utc_timestamp(cr, uid, self.date)
        result = re.match(self.pattern, timestamp)
        self.assertEquals(result.string, timestamp)

    @patch('pytz.timezone')
    def test_02_utc_timestamp_with_tz_in_context(self, timezone):
        cr, uid = self.cr, self.uid

        fields.datetime.utc_timestamp(cr, uid, self.date, context=self.context)
        self.assertEquals(timezone.call_count, 2)
        timezone.assert_any_call('UTC')
        timezone.assert_any_call('GB')
        timezone.localize.called_with(self.date)

    def test_03_utc_timestamp_with_tz_in_context_excepts_pytz_exceptions(self):
        cr, uid = self.cr, self.uid

        timestamp = fields.datetime.utc_timestamp(cr, uid, self.date,
                                                  context={'tz': '??'})
        result = re.match(self.pattern, timestamp)
        self.assertEquals(result.string, timestamp)
