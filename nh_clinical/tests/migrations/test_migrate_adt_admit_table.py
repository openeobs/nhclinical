# -*- coding: utf-8 -*-
from openerp.addons.nh_clinical.migrations import migrate_adt_admit_table
from openerp.tests.common import TransactionCase


class TestMigrateAdtAdmitTable(TransactionCase):

    def setUp(self):
        super(TestMigrateAdtAdmitTable, self).setUp()
        self.patient_model = self.env['nh.clinical.patient']
        self.registration_model = self.env['nh.clinical.adt.patient.register']
        self.test_utils = self.env['nh.clinical.test_utils']

        self.test_utils.create_locations()
        self.patients = []
        for i in range(3):
            patient = self.test_utils.create_and_register_patient()
            self.patients.append(patient)
            self.test_utils.admit_patient(patient_id=patient.id)
        self.patient_ids = map(lambda patient: patient.id, self.patients)

        domain = [
            ('patient_id', 'in', self.patient_ids)
        ]
        self.registrations = self.registration_model.search(domain)

    # def test_migrate_adt_admit_patient_id_column_to_registration(self):
    #     admit_model = self.env['nh.clinical.adt.patient.admit']
    #     domain = [
    #         ('registration.patient_id', 'in', self.patient_ids)
    #     ]
    #
    #     admissions_before = admit_model.search(domain)
    #     registrations_before = map(
    #         lambda admission: admission.registration,
    #         admissions_before
    #     )
    #     # Expecting all registration values to be `False`.
    #     # Invert booleans so can assert using `all()`.
    #     registrations_before = map(
    #         lambda registration: not registrations_before,
    #         registrations_before
    #     )
    #     self.assertTrue(all(registrations_before))
    #
    #     migrate_adt_admit_table.\
    #         migrate_adt_admit_patient_id_column_to_registrations(self.env.cr)
    #
    #     admissions_after = admit_model.search(domain)
    #     registrations_after = map(
    #         lambda admission: admission.registration,
    #         admissions_after
    #     )
    #
    #     self.assertEqual(self.registrations, registrations_after)

    def test_remove_patient_id_column_from_adt_admit_table(self):
        query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'nh_clinical_adt_patient_admit'
              AND column_name = 'patient_id'
        """
        self.env.cr.execute(query)
        results = self.env.cr.fetchall()
        self.assertTrue(results)

        migrate_adt_admit_table.\
            remove_patient_id_column_from_adt_admit_table(self.env.cr)

        self.env.cr.execute(query)
        results = self.env.cr.fetchall()
        self.assertFalse(results)
