# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import logging

from datetime import datetime as dt
from mock import MagicMock
from openerp.tests import common
from openerp.osv.orm import except_orm
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf

_logger = logging.getLogger(__name__)


class TestActivity(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestActivity, cls).setUpClass()
        cls.test_model_pool = cls.registry('test.activity.data.model')
        cls.activity_pool = cls.registry('nh.activity')
        cls.user_pool = cls.registry('res.users')
