# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase

from openerp.modules.loading import load_module_graph
from openerp.modules.graph import Graph


class TestOnePointZeroMigration(TransactionCase):

    def setUp(self):
        super(TestOnePointZeroMigration, self).setUp()
        self.test_utils = self.env['nh.clinical.test_utils']
        adt_admit_model = self.env['nh.clinical.adt.patient.admit']

        self.test_utils.create_locations()
        for i in range(3):
            self.test_utils.create_patient()
            adt_admit_model.create({
                'patient_id': adt_admit_model,
                'pos_id': self.test_utils.pos.id
            })

    def call_test(self):
        self.graph = Graph()
        self.graph.add_module(self.env.cr, 'nh_clinical')
        load_module_graph(self.graph)

    def test_migration(self):
        self.call_test()
