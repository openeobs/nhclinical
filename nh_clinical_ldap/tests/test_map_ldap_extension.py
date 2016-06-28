from openerp.tests.common import SingleTransactionCase


class TestMapLDAPExtension(SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestMapLDAPExtension, cls).setUpClass()
        cls.category_pool = cls.registry('res.partner.category')
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.ldap_pool = cls.registry('res.company.ldap')

        cls.ldap_entry = [
            None,
            {
                'cn': [
                    'Test User'
                ]
            }
        ]

        cls.conf = {
            'company': 1
        }

        def mock_category_search(*args, **kwargs):
            return [1]

        def mock_location_search(*args, **kwargs):
            context = kwargs.get('context')
            test = context.get('test') if context else ''
            if test == 'test_empty_location':
                return []
            return [666]

        def mock_pos_search(*args, **kwargs):
            context = kwargs.get('context')
            test = context.get('test') if context else ''
            if test == 'test_location':
                global location_passed
                location_passed = args[3]
            if test == 'test_empty_location':
                global empty_location
                empty_location = args[3]
            return [1]

        cls.category_pool._patch_method('search', mock_category_search)
        cls.location_pool._patch_method('search', mock_location_search)
        cls.pos_pool._patch_method('search', mock_pos_search)

    @classmethod
    def tearDownClass(cls):
        cls.category_pool._revert_method('search')
        cls.location_pool._revert_method('search')
        cls.pos_pool._revert_method('search')
        super(TestMapLDAPExtension, cls).tearDownClass()

    def test_hospital_passed_to_pos(self):
        """
        TEst that when a hospital is found it is then used to find the POS for
        that hospital
        """
        cr, uid = self.cr, self.uid
        self.ldap_pool.map_ldap_attributes(
            cr, uid, self.conf, 'test', self.ldap_entry,
            context={'test': 'test_location'})
        self.assertEqual(location_passed[0][2], [666])

    def test_empty_hospital_passed_to_pos(self):
        """
        TEst that when a hospital is not found it is then used to find the POS
        for that hospital
        """
        cr, uid = self.cr, self.uid
        self.ldap_pool.map_ldap_attributes(
            cr, uid, self.conf, 'test', self.ldap_entry,
            context={'test': 'test_empty_location'})
        self.assertEqual(empty_location, [['location_id', 'in', []]])

    def test_pos(self):
        """
        TEst that on POS found it then in the returned dict
        """
        cr, uid = self.cr, self.uid
        vals = self.ldap_pool.map_ldap_attributes(
            cr, uid, self.conf, 'test', self.ldap_entry,
            context={'test': 'test_pos'})
        self.assertEqual(vals.get('pos_ids'), [[6, 0, [1]]])

    def test_raises_on_invalid_ldap_entry(self):
        """
        TEst it raises value error when trying to map a non-conformant LDAP
        entry
        """
        cr, uid = self.cr, self.uid
        with self.assertRaises(ValueError) as ldap_err:
            self.ldap_pool.map_ldap_attributes(
                cr, uid, self.conf, 'test', [0])
        self.assertEqual(ldap_err.exception.message,
                         'LDAP Entry does not contain second element')

    def test_raises_on_invalid_ldap_entry_cn(self):
        """
        TEst it raises value error when trying to map a non-conformant LDAP
        entry
        """
        cr, uid = self.cr, self.uid
        with self.assertRaises(ValueError) as ldap_err:
            self.ldap_pool.map_ldap_attributes(
                cr, uid, self.conf, 'test', [None, {'cn': []}])
        self.assertEqual(ldap_err.exception.message,
                         'LDAP Entry CN does not contain elements')
