# -*- coding: utf-8 -*-
# Part of NHClinical. See LICENSE file for full copyright and licensing details
from . import cookie_fix
from . import fix_odoo8_fields_many2many_set
from . import fix_read_group_fill_results
from . import fix_server_shutdown_issue
from . import orm_fixes
from . import remove_exception_name_from_error_dialogs
from . import validate
from .models import datetime_utils

from .tests import common