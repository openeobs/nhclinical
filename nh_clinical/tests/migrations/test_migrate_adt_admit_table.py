# -*- coding: utf-8 -*-
"""
These tests were created for the purposes of TDD whilst creating the migration
scripts. They will only work properly under certain conditions.

    1. Have an pre-migration environment.
    2. Check out the new code containing this test and the migration scripts.
    3. The version in `__openerp__.py` is updated to 1.0 by the new code.
       Change it back to what it was before.
    4. Now you can run the tests without the migration occurring.
"""
from openerp.addons.nh_clinical.migrations import migrate_adt_admit_table
from openerp.tests.common import TransactionCase


class TestMigrateAdtAdmitTable(TransactionCase):

    def setUp(self):
        super(TestMigrateAdtAdmitTable, self).setUp()
        self.patient_model = self.env['nh.clinical.patient']
        self.registration_model = self.env['nh.clinical.adt.patient.register']
        self.admit_model = self.env['nh.clinical.adt.patient.admit']
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

    def test_migrate_adt_admit_patient_id_column_to_registration(self):
        """
        There is an important assumption in this test that updating the admit
        table using SQL will be effective in updating the records used in the
        application logic.

        The reason this assumption exists is because after updating via SQL,
        searches do not appear to find the records.
        """
        domain = [
            ('registration.patient_id', 'in', self.patient_ids)
        ]
        admissions_before = self.admit_model.search(domain)
        admission_ids = map(lambda a: a.id, admissions_before)
        # Set patient ID to simulate a record from before migration.
        for admission in admissions_before:
            self.env.cr.execute("""
                UPDATE nh_clinical_adt_patient_admit AS admit
                SET patient_id = {patient_id}
                WHERE id = {admission_id}
                ;
            """.format(
                    patient_id=admission.registration.patient_id.id,
                    admission_id=admission.id
                )
            )
        # Set registration to `None` to simulate a record from before
        # migration.
        for admission in admissions_before:
            admission.registration = None

        # Expecting all registration values to be `False`.
        # Invert booleans so can assert using `all()`.
        registration_values_before = map(
            lambda a: not a.registration,
            admissions_before
        )
        self.assertTrue(all(registration_values_before))

        migrate_adt_admit_table.\
            migrate_adt_admit_patient_id_column_to_registrations(self.env.cr)

        # Had to use `read` instead of `browse` as it would return an empty
        # recordset for the registration as though it did not recognise the
        # changes made by the SQL. Tried clearing the cache using
        # `clear_caches` but it had no effect.
        admissions_after = self.admit_model.browse(admission_ids).read()
        registrations_ids = map(lambda a: a['registration'][0],
                                admissions_after)
        registrations_after = self.registration_model.browse(registrations_ids)

        self.assertEqual(self.registrations, registrations_after)

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
