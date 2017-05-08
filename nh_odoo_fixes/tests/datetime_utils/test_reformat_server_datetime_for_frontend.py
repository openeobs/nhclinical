# -*- coding: utf-8 -*-
from datetime import datetime

from openerp.tests.common import TransactionCase
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class TestReformatServerDatetimeForFrontend(TransactionCase):

    def setUp(self):
        super(TestReformatServerDatetimeForFrontend, self).setUp()
        self.datetime_utils = self.env['datetime_utils']

    def test_converts_to_client_timezone(self):
        date_time = datetime(year=1989, month=06, day=06, hour=13)
        date_time_str = date_time.strftime(DTF)
        context_with_timezone = {'tz': 'Europe/London'}

        expected = '14:00 06/06/1989'
        actual = self.datetime_utils.reformat_server_datetime_for_frontend(
            date_time_str, context_with_timezone=context_with_timezone)
        self.assertEqual(expected, actual)
