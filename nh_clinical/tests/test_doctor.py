import logging

from openerp.tests import common
from openerp.osv.orm import except_orm

_logger = logging.getLogger(__name__)


class TestClinicalDoctor(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestClinicalDoctor, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.doctor_pool = cls.registry('nh.clinical.doctor')
        cls.partner_pool = cls.registry('res.partner')

    def test_01_evaluate_doctors_dict(self):
        cr, uid = self.cr, self.uid

        doctors = """[{
            'type': 'c',
            'code': 'CON01',
            'title': 'Dr.',
            'given_name': 'Consulting',
            'family_name': 'Doctor',
            'gender': 'F'
        }, {
            'type': 'r',
            'code': 'REF01',
            'title': 'dr.',
            'given_name': 'Referring',
            'family_name': 'Doctor',
            'gender': 'M'
        }]"""

        data = {'doctors': doctors}

        # Scenario 1: Evaluate doctors and create them
        self.assertTrue(self.doctor_pool.evaluate_doctors_dict(cr, uid, data))
        con_id = self.doctor_pool.search(cr, uid, [['code', '=', 'CON01']])
        self.assertTrue(con_id, msg="Consulting Doctor not created")
        ref_id = self.doctor_pool.search(cr, uid, [['code', '=', 'REF01']])
        self.assertTrue(ref_id, msg="Referring Doctor not created")
        self.assertEqual([[6, False, con_id]], data.get('con_doctor_ids'))
        self.assertEqual([[6, False, ref_id]], data.get('ref_doctor_ids'))

        # Scenario 2: Evaluate doctors and read them
        self.assertTrue(self.doctor_pool.evaluate_doctors_dict(cr, uid, data))
        self.assertEqual([[6, False, con_id]], data.get('con_doctor_ids'))
        self.assertEqual([[6, False, ref_id]], data.get('ref_doctor_ids'))

        # Scenario 3: Evaluate without doctors
        self.assertFalse(self.doctor_pool.evaluate_doctors_dict(cr, uid, {}))