# -*- coding: utf-8 -*-
from datetime import datetime

from openerp.tests.common import TransactionCase

from openerp.addons.nh_odoo_fixes import validate

class TestNotInTheFuture(TransactionCase):

    def test_now_does_not_raise_exception(self):
        validate.not_in_the_future(datetime.now())
