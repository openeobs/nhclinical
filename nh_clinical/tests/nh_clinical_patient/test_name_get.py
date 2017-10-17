from openerp.tests.common import SingleTransactionCase


class TestPatientNameGet(SingleTransactionCase):
    """
    Test that the name_get method on nh.clinical.patient.
    """

    @classmethod
    def setUpClass(cls):
        super(TestPatientNameGet, cls).setUpClass()
        cls.patient_pool = cls.registry('nh.clinical.patient')
        cls.patient_id = cls.patient_pool.create(cls.cr, cls.uid, {
            'family_name': 'Wren',
            'given_name': 'Colin',
            'other_identifier': 'HOSPTESTPATIENT'
        })

        def mock_patient_fullname(*args, **kwargs):
            global fullname_called
            fullname_called = True
            return mock_patient_fullname.origin(*args, **kwargs)

        cls.patient_pool._patch_method('_get_fullname', mock_patient_fullname)

    @classmethod
    def tearDownClass(cls):
        cls.patient_pool._revert_method('_get_fullname')
        super(TestPatientNameGet, cls).tearDownClass()

    def test_name_get(self):
        """
        Test that the name_function returns the correct name.
        """
        cr, uid = self.cr, self.uid
        patient = self.patient_pool.name_get(cr, uid, self.patient_id)
        self.assertEqual(patient, [(self.patient_id, 'Wren, Colin')])
        self.assertTrue(fullname_called)

    def test_name_get_update(self):
        """
        Test that on updating the patient record the name_get is reflecting
        the change.
        """
        cr, uid = self.cr, self.uid
        patient = self.patient_pool.name_get(cr, uid, self.patient_id)
        self.assertEqual(patient, [(self.patient_id, 'Wren, Colin')])
        self.patient_pool.write(cr, uid, self.patient_id, {
            'middle_names': 'Frank'
        })
        update = self.patient_pool.name_get(cr, uid, self.patient_id)
        self.assertEqual(update, [(self.patient_id, 'Wren, Colin Frank')])
