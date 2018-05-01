from openerp.tests.common import SavepointCase


class TestAllocationComplete(SavepointCase):

    def setUp(self):
        super(TestAllocationComplete, self).setUp()
        self.test_utils_model = self.env['nh.clinical.test_utils']
        self.test_utils_model.setup_ward()
        self.test_utils_model.create_patient()
        self.test_utils_model.copy_instance_variables(self)

        self.admission_model = self.env['nh.clinical.patient.admission']
        self.move_model = self.env['nh.clinical.patient.move']
        self.activity_model = self.env['nh.activity']

    def test_creates_move_record(self):
        move_records_for_patient_before = self.move_model.search([
            ('patient_id', '=', self.patient.id)
        ])

        admission_activity_id = self.admission_model.create_activity(
            {},
            {
                'patient_id': self.patient.id,
                'pos_id': self.pos.id,
                'location_id': self.ward.id
            }
        )
        admission_activity = self.activity_model.browse(admission_activity_id)
        admission_activity.complete()

        move_records_for_patient_after = self.move_model.search([
            ('patient_id', '=', self.patient.id)
        ])
        self.assertEqual(
            len(move_records_for_patient_before) + 1,
            len(move_records_for_patient_after)
        )

    def test_move_record_has_correct_admission_date(self):
        expected_start_date = '2015-04-30 17:00:00'
        admission_activity_id = self.admission_model.create_activity(
            {},
            {
                'patient_id': self.patient.id,
                'pos_id': self.pos.id,
                'location_id': self.ward.id,
                'start_date': expected_start_date
            }
        )
        admission_activity = self.activity_model.browse(admission_activity_id)
        admission_activity.complete()

        latest_move_record = self.move_model.search([
            ('patient_id', '=', self.patient.id)
        ], limit=1)
        self.assertEqual(
            expected_start_date,
            latest_move_record.move_datetime
        )
