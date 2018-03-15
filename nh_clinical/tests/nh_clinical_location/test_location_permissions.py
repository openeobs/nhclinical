from openerp.exceptions import AccessError
from openerp.tests.common import TransactionCase


class TestLocationPermissions(TransactionCase):
    def setUp(self):
        super(TestLocationPermissions, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.test_utils.admit_and_place_patient()
        self.location_model = self.env['nh.clinical.location']

    def test_shift_coordinator_cannot_create(self):
        shift_coordinator = self.test_utils.create_shift_coordinator()
        with self.assertRaises(AccessError):
            self.location_model\
                .sudo(shift_coordinator)\
                .create({'name': 'Albuquerque'})

    # EOBS-2359
    def test_shift_coordinator_cannot_edit(self):
        shift_coordinator = self.test_utils.create_shift_coordinator()
        with self.assertRaises(AccessError):
            self.test_utils.ward.sudo(shift_coordinator).name = 'Waldo Ward'

    def test_shift_coordinator_cannot_delete(self):
        shift_coordinator = self.test_utils.create_shift_coordinator()
        with self.assertRaises(AccessError):
            self.test_utils.ward.sudo(shift_coordinator).unlink()

    def test_superuser_can_create(self):
        self.location_model.create({'name': 'Mississippi'})

    def test_superuser_can_edit(self):
        self.test_utils.ward.name = 'Wilfred Ward'

    def test_superuser_can_delete(self):
        self.test_utils.bed.unlink()

    def test_system_admin_can_create(self):
        system_admin = self.test_utils.create_system_admin()
        self.location_model.sudo(system_admin).create({'name': 'Ohio'})

    def test_system_admin_can_edit(self):
        system_admin = self.test_utils.create_system_admin()
        self.test_utils.ward.sudo(system_admin).name = 'Wilma Ward'

    def test_system_admin_can_delete(self):
        system_admin = self.test_utils.create_system_admin()
        self.test_utils.bed.sudo(system_admin).unlink()
