from openerp.tests.common import SingleTransactionCase


class TestManualMergeViaErppeek(SingleTransactionCase):
    def setUp(self):
        self.test_utils = self.env['nh.clinical.test_utils']

        self.test_utils.admit_and_place_patient()
        self.from_patient = self.test_utils.patient

        self.test_utils.create_patient()
        self.to_patient = self.test_utils.patient

        self.patient_model = self.env['nh.clinical.patient']
        self.activity_model = self.env['nh.activity']

    def test_manual_merge(self):
        domain = [
            ('patient_id', '=', self.from_patient.id)
        ]
        from_patient_activities = self.activity_model.search(domain)

        domain = [
            ('patient_id', '=', self.to_patient.id)
        ]
        too_patient_activities = self.activity_model.search(domain)

        from_patient_activities.write({'patient_id': self.to_patient.id})

        from_patient_vals = self.from_patient.read()[0]
        # field_names = [field_name for field_name in from_patient_vals.keys()
        #                if field_name not in MAGIC_COLUMNS]

        self.to_patient.write(from_patient_vals)

        self.from_patient.active = False
