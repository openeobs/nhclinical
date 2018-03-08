# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase


# EOBS-549, EOBS-2378
class TestFieldsViewGet(TransactionCase):
    """
    Test the field_view_get method override. This method returns a definition
    of the field which determines how it is displayed and how it behaves.
    Specifically this override is used to change the `domain` property of the
    field definition so that the when populating the field the users that are
    returned as part of the autocomplete feature are limited to only those
    users that are eligible for that field (nurses for the nurse field and
    hcas for the hca field).
    """
    def setUp(self):
        super(TestFieldsViewGet, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        # Creates locations and users.
        self.test_utils.admit_and_place_patient()
        self.shift_coordinator = self.test_utils.create_shift_coordinator()
        self.nurse = self.test_utils.nurse
        self.hca = self.test_utils.hca
        self.nurse_2 = self.test_utils.create_nurse(allocate=False)
        self.hca_2 = self.test_utils.create_hca(allocate=False)

        self.expected_nurse_ids_available_for_allocation = map(
            lambda e: e.id, [
                self.nurse, self.nurse_2
            ]
        )
        self.expected_hca_ids_available_for_allocation = map(
            lambda e: e.id, [
                self.hca, self.hca_2
            ]
        )
        user_model = self.env['res.users']
        # Expected needs to be a recordset to match actual result type.
        self.expected_nurses_available_for_allocation = \
            user_model.browse(self.expected_nurse_ids_available_for_allocation)
        self.expected_hcas_available_for_allocation = \
            user_model.browse(self.expected_hca_ids_available_for_allocation)

    def call_test(self, wizard_type='allocation', vaccuum_wizards=False):
        self.allocation_model = self.env['nh.clinical.staff.allocation']\
            .sudo(self.shift_coordinator)
        self.allocation = self.allocation_model.create({})
        # Have to assign users after creation because setting in creation
        # dictionary does not work. Not sure why.
        self.allocation.ward_id = self.test_utils.ward.id
        self.allocation.user_ids = \
            self.expected_nurses_available_for_allocation \
            + self.expected_hcas_available_for_allocation
        self.allocation.complete()

        if wizard_type == 'reallocation':
            self.reallocation_model = \
                self.env['nh.clinical.staff.reallocation']\
                    .sudo(self.shift_coordinator)
            self.reallocation_model.create({})

        if vaccuum_wizards:
            self.allocation_model.search([]).unlink()
            self.reallocation_model.search([]).unlink()

        allocating_model = self.env['nh.clinical.allocating']\
            .sudo(self.shift_coordinator)\
            .with_context({'parent_view': wizard_type})
        fields_view = allocating_model.fields_view_get(view_type='form')

        self.nurse_id_field_domain = \
            fields_view['fields']['nurse_id']['domain']
        self.hca_id_field_domain = fields_view['fields']['hca_ids']['domain']
        self.nurse_ids = self.nurse_id_field_domain[0][2]
        self.hca_ids = self.hca_id_field_domain[0][2]
        self.allocation_expected_hca_group_domain_parameter = \
            ['groups_id.name', 'in', ['NH Clinical HCA Group']]
        self.allocation_expected_nurse_group_domain_parameter = \
            ['groups_id.name', 'in', ['NH Clinical Nurse Group']]

    def test_returns_nurses_added_to_roll_call_during_allocation(self):
        """
        Only the nurses assigned to the shift are returned as autocomplete
        options in the allocating view.
        """
        self.call_test(wizard_type='allocation')
        self.assertEqual(
            sorted(self.expected_nurse_ids_available_for_allocation +
                   self.expected_hca_ids_available_for_allocation),
            sorted(self.nurse_ids)
        )
        self.assertTrue(
            self.allocation_expected_nurse_group_domain_parameter in
            self.nurse_id_field_domain)

    def test_returns_hcas_added_to_roll_call_during_allocation(self):
        """
        Only the HCAs assigned to the shift are returned as autocomplete
        options in the allocating view.
        """
        self.call_test(wizard_type='allocation')
        self.assertEqual(
            sorted(self.expected_nurse_ids_available_for_allocation +
                   self.expected_hca_ids_available_for_allocation),
            sorted(self.hca_ids)
        )
        self.assertTrue(
            self.allocation_expected_hca_group_domain_parameter in
            self.hca_id_field_domain)

    def test_returns_nurses_added_to_roll_call_during_reallocation(self):
        """
        Only the nurses assigned to the shift are returned as autocomplete
        options in the allocating view.
        """
        self.call_test(wizard_type='reallocation')
        self.assertEqual(
            sorted(self.expected_nurse_ids_available_for_allocation),
            sorted(self.nurse_ids)
        )

    def test_returns_hcas_added_to_roll_call_during_reallocation(self):
        """
        Only the HCAs assigned to the shift are returned as autocomplete
        options in the allocating view.
        """
        self.call_test(wizard_type='reallocation')
        self.assertEqual(
            sorted(self.expected_hca_ids_available_for_allocation),
            sorted(self.hca_ids)
        )

    def test_returns_nurses_added_to_roll_call_when_no_wizards_exist(self):
        self.call_test(wizard_type='reallocation', vaccuum_wizards=True)
        self.assertEqual(
            sorted(self.expected_nurse_ids_available_for_allocation),
            sorted(self.nurse_ids)
        )
