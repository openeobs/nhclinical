# -*- coding: utf-8 -*-
import uuid

from openerp.addons.nh_clinical.migrations import \
    backdate_registrations as br
from openerp.tests.common import TransactionCase


class TestBackdateRegistrationsFromAdmissions(TransactionCase):

    def setUp(self):
        super(TestBackdateRegistrationsFromAdmissions, self).setUp()
        self.patient_model = self.env['nh.clinical.patient']
        self.registration_model = self.env['nh.clinical.adt.patient.register']
        self.test_utils = self.env['nh.clinical.test_utils']

        self.registration_model.search([]).unlink()
        # Cannot use unlink on patient as it is overridden to retain data.
        self.env.cr.execute("TRUNCATE TABLE nh_clinical_patient CASCADE;")

        self.patients = []
        self.patients_without_registrations = []
        for i in range(6):
            if i % 2 == 0:
                self.patients.append(
                    self.test_utils.create_and_register_patient())
            else:
                patient = self.test_utils.create_patient()
                self.patients.append(patient)
                self.patients_without_registrations.append(patient)
        self.patient_without_registrations = \
            tuple([patient.id for patient in self.patients])

        self.number_of_patients = 6
        self.number_of_registrations = 3
        self.number_of_patients_without_registrations = \
            self.number_of_patients - self.number_of_registrations

        self.assertEqual(
            self.number_of_registrations,
            len(self.registration_model.search([]))
        )

    def test_get_patients_for_whom_no_registration_exists(self):
        expected_number_of_patients = 3
        actual_number_of_patients = \
            len(br.get_ids_for_patients_without_registrations(self.env.cr))
        self.assertEqual(
            expected_number_of_patients, actual_number_of_patients)

    def test_create_registrations_for_patients_adds_expected_number_of_rows(
            self):
        patient_ids = tuple([patient.id for patient in
                             self.patients_without_registrations])
        br.create_registrations_for_patients(self.env.cr, patient_ids)

        expected = self.number_of_registrations \
                   + self.number_of_patients_without_registrations
        actual = len(self.registration_model.search([]))

        self.assertEqual(expected, actual)

    def test_created_registrations_are_correct(self):
        patient_ids = tuple([patient.id for patient in
                             self.patients_without_registrations])
        br.create_registrations_for_patients(self.env.cr, patient_ids)

        def extract_common_keys(item):
            return {
                'family_name': item['family_name'],
                'given_name': item['given_name'],
                'patient_identifier': item['patient_identifier']
            }

        patients = map(lambda patient: patient.read()[0], self.patients)
        patients = map(extract_common_keys, patients)
        patients = sorted(patients, key=lambda i: i['patient_identifier'])

        registrations = self.registration_model.search([]).read()
        registrations = map(extract_common_keys, registrations)
        registrations = sorted(registrations,
                               key=lambda i: i['patient_identifier'])

        self.assertEqual(patients, registrations)

    def test_create_registrations_for_patients_creates_no_rows_if_error(self):
        self.assertEqual(self.number_of_registrations,
                         len(self.registration_model.search([])))

        # Induce an error by passing a non-existent patient ID.
        patient_id = str(uuid.uuid4().int)
        patient_ids = tuple([patient_id])
        br.create_registrations_for_patients(self.env.cr, patient_ids)

        self.assertEqual(self.number_of_registrations,
                         len(self.registration_model.search([])))
