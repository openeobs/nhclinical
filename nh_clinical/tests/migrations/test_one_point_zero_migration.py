# -*- coding: utf-8 -*-
from openerp.modules.graph import Graph
from openerp.modules.loading import load_module_graph
from openerp.tests.common import TransactionCase


class TestOnePointZeroMigration(TransactionCase):

    def setUp(self):
        super(TestOnePointZeroMigration, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        self.adt_admit_model = self.env['nh.clinical.adt.patient.admit']

        self.test_utils.create_locations()
        for i in range(3):
            patient = self.test_utils.create_patient()
            self.adt_admit_model.create({
                'patient_id': patient.id,
                'pos_id': self.test_utils.pos.id
            })

    def test_migration(self):
        all_adt_admit_patient_ids = self.adt_admit_model.search_read(
            [], fields=['patient_id'])

        self.assert_field_and_columns_correct_before()
        self._migrate()
        self.assert_field_and_columns_correct_after()

        self.assert_data_integrity_after(all_adt_admit_patient_ids)

    def _migrate(self):
        self.graph = Graph()
        self.graph.add_module(self.env.cr, 'nh_clinical')
        load_module_graph(self.graph)

    def assert_field_and_columns_correct_before(self):
        self.assert_field_and_columns_correct(True)

    def assert_field_and_columns_correct_after(self):
        self.assert_field_and_columns_correct(False)

    def assert_field_and_columns_correct(self, boolean):
        expected_field = 'patient_id'
        not_expected_field = 'registration'

        field_exists = self.test_utils.field_exists(
            'nh.clinical.adt.patient.admit', expected_field)
        self.assertEqual(field_exists, boolean)

        field_exists = self.test_utils.field_exists(
            'nh.clinical.adt.patient.admit', not_expected_field)
        self.assertFalse(field_exists, boolean)

        self.env.cr.execute("""
            select column_name
            from information_schema.columns
            where table_name = 'nh_clinical_adt_patient_admit'
              and column_name = {}
            ;
        """.format(expected_field))
        records = self.env.cr.fetchall()

        self.env.cr.execute("""
            select column_name
            from information_schema.columns
            where table_name = 'nh_clinical_adt_patient_admit'
              and column_name = {}
            ;
        """.format(expected_field))
        records = self.env.cr.fetchall()

    def assert_data_integrity_after(self, adt_admit_dictionaries):
        """
        Assert that the ADT admit records are still fundamentally related to
        the same patients.

        Before `patient_id` was a related field directly on the ADT admit
        model but it is still accessible with one more step via the
        registration related field that has replaced the original `patient_id`
        field.

        :param adt_admit_dictionaries:
        :return:
        """
        before_patient_ids = \
            map(lambda d: d['patient_id'], adt_admit_dictionaries)
        after_patient_ids = []

        for dictionary in adt_admit_dictionaries:
            record = self.adt_admit_model.browse(dictionary['id'])
            patient_id_from_registration = record.registration.patient_id.id
            after_patient_ids.append(patient_id_from_registration)

        self.assertEqual(before_patient_ids, after_patient_ids)
