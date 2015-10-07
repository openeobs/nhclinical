from openerp.tests.common import SingleTransactionCase

class TestUsers(SingleTransactionCase):

    def setUp(self):
        """***setup user management tests***"""
        super(TestUsers, self).setUp()
        cr, uid, = self.cr, self.uid

        self.users_pool = self.registry('res.users')
        self.groups_pool = self.registry('res.groups')
        self.activity_pool = self.registry('nh.activity')
        self.location_pool = self.registry('nh.clinical.location')
        self.responsibility_allocation = self.registry('nh.clinical.responsibility.allocation')
        self.apidemo = self.registry('nh.clinical.api.demo')

    def test_responsibility_allocation(self):
        cr, uid = self.cr, self.uid
        users = {
            'ward_managers': {
                'wm1': ['wm1', 'U'],
                'wm2': ['wm2', 'T']
            },
            'nurses': {
                'nurse1': ['nurse1', ['U0', 'U1']],
                'nurse2': ['nurse2', ['T0', 'T1']]
            },
            'hcas': {
                'hca1': ['hca1', ['U0', 'U1', 'T0', 'T1']]
            },
            'doctors': {
                'doctor1': ['doctor1', ['U0', 'U1', 'T0', 'T1']]
            }
        }

        self.apidemo.build_unit_test_env1(cr, uid, users=users)

        wm1_id = self.users_pool.search(cr, uid, [('login', '=', 'wm1')])[0]

        nurse1_id = self.users_pool.search(cr, uid, [('login', '=', 'nurse1')])[0]

        ward_U_id = self.location_pool.search(cr, uid, [('code', '=', 'U')])[0]
        ward_T_id = self.location_pool.search(cr, uid, [('code', '=', 'T')])[0]

        # Adding and Removing a ward responsibility to a ward manager
        ra_id = self.responsibility_allocation.create(cr, uid, {'user_id': wm1_id, 'location_ids': [[6, False, [ward_T_id, ward_U_id]]]})
        self.responsibility_allocation.submit(cr, uid, [ra_id])
        spell_ids = self.activity_pool.search(cr, uid, [('data_model', '=', 'nh.clinical.spell'), ('location_id', 'in', [ward_U_id, ward_T_id])])
        for spell_id in spell_ids:
            self.assertTrue(self.activity_pool.search(cr, uid, [('id', '=', spell_id), ('user_ids', 'in', [wm1_id])]))
        ra_id = self.responsibility_allocation.create(cr, uid, {'user_id': wm1_id, 'location_ids': [[6, False, [ward_U_id]]]})
        self.responsibility_allocation.submit(cr, uid, [ra_id])
        spell_ids = self.activity_pool.search(cr, uid, [('data_model', '=', 'nh .clinical.spell'), ('location_id', 'in', [ward_T_id])])
        for spell_id in spell_ids:
            self.assertFalse(self.activity_pool.search(cr, uid, [('id', '=', spell_id), ('user_ids', 'in', [wm1_id])]))
        # Adding and Removing responsibilities to a nurse
        ra_id = self.responsibility_allocation.create(cr, uid, {'user_id': nurse1_id, 'location_ids': [[6, False, [ward_T_id]]]})
        self.responsibility_allocation.submit(cr, uid, [ra_id])
        observation_ids = self.activity_pool.search(cr, uid, [('data_model', 'ilike', '%observation%'), ('location_id', 'child_of', [ward_T_id])])
        notification_ids = self.activity_pool.search(cr, uid, [('data_model', 'ilike', '%notification%'), ('location_id', 'child_of', [ward_T_id])])
        for activity_id in observation_ids+notification_ids:
            self.assertTrue(self.activity_pool.search(cr, uid, [('id', '=', activity_id), ('user_ids', 'in', [nurse1_id])]))
        observation_ids = self.activity_pool.search(cr, uid, [('data_model', 'ilike', '%observation%'), ('location_id', 'child_of', [ward_U_id])])
        notification_ids = self.activity_pool.search(cr, uid, [('data_model', 'ilike', '%notification%'), ('location_id', 'child_of', [ward_U_id])])
        for activity_id in observation_ids+notification_ids:
            self.assertFalse(self.activity_pool.search(cr, uid, [('id', '=', activity_id), ('user_ids', 'in', [nurse1_id])]))
