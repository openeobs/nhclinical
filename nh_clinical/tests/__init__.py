# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-

# Base level tests
from . import test_location
from . import test_operations
from . import test_user_management
from . import test_api_demo
from . import test_activity_extension
from . import test_base_extensions
from . import test_patient_placement_wizard
from . import test_responsibility_allocation_wizard
from . import test_users

# Test Patient
from . import test_patient
from . import test_patient_name_get

# Test Staff Allocation
from . import test_staff_allocation_submit_wards
from . import test_staff_allocation_deallocate
from . import test_staff_allocation_submit_users
from . import test_staff_allocation_complete
from . import test_allocation_unfollow
from . import test_allocation_responsibility_allocation

# Test Staff Reallocation
from . import test_staff_reallocation_default_ward
from . import test_staff_reallocation_default_locations
from . import test_staff_reallocation_default_users
from . import test_staff_reallocation_default_allocatings
from . import test_staff_reallocation_reallocate
from . import test_staff_reallocation_complete
from . import test_get_allocation_locations

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
