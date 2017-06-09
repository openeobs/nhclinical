# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-

# Base level tests
from .nh_activity import *
from . import test_api_demo
from . import test_base_extensions
from . import test_location
from . import test_operations
from . import test_patient_placement_wizard
from . import test_responsibility_allocation_wizard
from . import test_users

from .nh_clinical_doctor_allocation import *
from .nh_clinical_patient import *
from .nh_clinical_staff_allocation import *
from .nh_clinical_staff_reallocation import *
from .res_user import *
from .nh_clinical_user_management import *
from .nh_clinical_spell import *

# Disabled Tests
# from . import test_doctor
# from . import test_spell
# from . import test_auditing
# from . import test_devices
# from . import test_adt
# from . import test_api
# from . import test_patient_register
# from . import test_patient_update
# from . import test_patient_admit
# from . import test_user_allocation
# from . import test_allocation_wizards
