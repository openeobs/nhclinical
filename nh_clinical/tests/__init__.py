# -*- coding: utf-8 -*-
# Part of NHClinical. See LICENSE file for full copyright and licensing details

from . import test_api_demo
from . import test_base_extensions
from . import test_devices
from . import test_doctor
from . import test_location
from . import test_operations
from . import test_patient_placement_wizard
from . import test_responsibility_allocation_wizard
from . import test_users
from .nh_activity import *
from .nh_clinical_adt import *
from .nh_clinical_api import *
from .nh_clinical_doctor_allocation import *
from .nh_clinical_patient import *
from .nh_clinical_patient_transfer import *
from .nh_clinical_spell import *
from .nh_clinical_staff_allocation import *
from .nh_clinical_staff_reallocation import *
from .nh_clinical_user_management import *
from .res_user import *

# Disabled Tests
# from . import test_auditing
# from . import test_user_allocation
# from . import test_allocation_wizards
# from . import test_allocation_responsibility_allocation
# from . import test_allocation_unfollow
# from . import test_base
# from . import test_data_formatter
# from . import test_get_allocation_locations
# from . import test_model
# from . import test_new_demo
