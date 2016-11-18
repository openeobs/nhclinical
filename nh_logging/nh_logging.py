# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import logging
import threading

import os
from openerp.netsvc import DBFormatter


def new_format(self, record):
    current_pid = os.getpid()
    current_thread = threading.currentThread()
    current_db = getattr(current_thread, 'dbname', '?')
    current_uid = getattr(current_thread, 'uid', '?')
    record.pid = current_pid
    record.dbname = '{0} on {1}'.format(current_uid, current_db)
    return logging.Formatter.format(self, record)


DBFormatter.format = new_format
