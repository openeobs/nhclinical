from openerp.tests.common import SingleTransactionCase


class TestStaffReallocationDefaultUsers(SingleTransactionCase):

    BEDS = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    USERS = [1337]

    @classmethod
    def setUpClass(cls):
        super(TestStaffReallocationDefaultUsers, cls).setUpClass()
        cls.users_pool = cls.registry('res.users')
        cls.allocation_pool = cls.registry('nh.clinical.staff.reallocation')

        def mock_get_default_locations(*args, **kwargs):
            context = kwargs.get('context')
            if context and context == 'check_get_locations':
                global location_called
                location_called = True
            return cls.BEDS

        def mock_users_search(*args, **kwargs):
            context = kwargs.get('context')
            if context:
                if context == 'check_methods':
                    return []
                if context == 'check_search':
                    global users_search
                    users_search = args[3]
            return cls.USERS

        cls.allocation_pool._patch_method('_get_default_locations',
                                          mock_get_default_locations)
        cls.users_pool._patch_method('search', mock_users_search)

    @classmethod
    def tearDownClass(cls):
        cls.allocation_pool._revert_method('_get_default_locations')
        cls.users_pool._revert_method('search')
        super(TestStaffReallocationDefaultUsers, cls).tearDownClass()

    def test_calls_get_default_locations(self):
        """
        Test that it calls get_default_location
        """
        self.allocation_pool._get_default_users(self.cr, self.uid,
                                                context='check_get_locations')
        self.assertTrue(location_called)

    def test_uses_location_ids_in_search(self):
        """
        Test that it uses location IDs when searching for users
        """
        self.allocation_pool._get_default_users(self.cr, self.uid,
                                                context='check_search')
        self.assertEqual(users_search[0],
                         ['groups_id.name', 'in',
                          self.allocation_pool._nursing_groups])
        self.assertEqual(users_search[1],
                         ['location_ids', 'in', self.BEDS])

    def test_returns_users(self):
        """
        Test that it returns the users it finds
        """
        users = self.allocation_pool._get_default_users(self.cr, self.uid)
        self.assertEqual(users, self.USERS)
