import logging
from openerp.tests import common
_logger = logging.getLogger(__name__)


class TestDemoAPI(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestDemoAPI, cls).setUpClass()
        cr, uid = cls.cr, cls.uid
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.apidemo = cls.registry('nh.clinical.api.demo')

        cls.pos_location_id = cls.location_pool.create(cr, uid, {
            'name': 'Test POS',
            'code': 'POS',
            'type': 'pos',
            'usage': 'hospital'
        })
        cls.pos_id = cls.pos_pool.create(cr, uid, {'name': 'Test POS', 'location_id': cls.pos_location_id})
        cls.location_pool.write(cr, uid, cls.pos_location_id, {'pos_id': cls.pos_id})

    def test_create_ward(self):
        cr, uid = self.cr, self.uid
        result = self.apidemo.create_ward(cr, uid, 'Test Ward', self.pos_location_id, 'TW', 10)
        ward = self.location_pool.browse(cr, uid, result['ward_id'])
        self.assertTrue(result['ward_id'], msg="Ward was not created")
        self.assertTrue(ward.name == 'Test Ward', msg="Ward name not correct")
        self.assertTrue(ward.code == 'TW', msg="Ward code not correct")
        self.assertTrue(ward.parent_id.id == self.pos_location_id, msg="Ward parent not correct")
        self.assertTrue(len(result['bed_ids']) == 10, msg="Incorrect number of beds")
        self.assertTrue(len(ward.child_ids) == 10, msg="Incorrect number of beds")