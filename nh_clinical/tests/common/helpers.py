# -*- coding: utf-8 -*-
def create_test_data(cls, cr, uid, iterations=3):
    cls.users_pool = cls.registry('res.users')
    cls.groups_pool = cls.registry('res.groups')
    cls.activity_pool = cls.registry('nh.activity')
    cls.location_pool = cls.registry('nh.clinical.location')
    cls.patient_pool = cls.registry('nh.clinical.patient')
    cls.api_pool = cls.registry('nh.clinical.api')
    cls.pos_pool = cls.registry('nh.clinical.pos')
    cls.responsibility_allocation = cls.registry(
        'nh.clinical.responsibility.allocation')
    cls.staff_allocation = cls.registry('nh.clinical.staff.allocation')
    cls.staff_reallocation = cls.registry('nh.clinical.staff.reallocation')
    cls.doctor_allocation = cls.registry('nh.clinical.doctor.allocation')
    cls.allocating = cls.registry('nh.clinical.allocating')
    cls.follow_pool = cls.registry('nh.clinical.patient.follow')
    cls.unfollow_pool = cls.registry('nh.clinical.patient.unfollow')

    cls.wm_group_id = cls.groups_pool.search(
        cr, uid, [['name', '=', 'NH Clinical Shift Coordinator Group']])
    cls.nurse_group_id = cls.groups_pool.search(
        cr, uid, [['name', '=', 'NH Clinical Nurse Group']])
    cls.hca_group_id = cls.groups_pool.search(
        cr, uid, [['name', '=', 'NH Clinical HCA Group']])
    cls.doctor_group_id = cls.groups_pool.search(
        cr, uid, [['name', '=', 'NH Clinical Doctor Group']])
    cls.admin_group_id = cls.groups_pool.search(
        cr, uid, [['name', '=', 'NH Clinical Admin Group']])

    cls.hospital_id = cls.location_pool.create(
        cr, uid, {'name': 'Test Hospital', 'code': 'TESTHOSP',
                  'usage': 'hospital'})
    cls.pos_id = cls.pos_pool.create(
        cr, uid, {'name': 'Test POS', 'location_id': cls.hospital_id})

    cls.admin_uid = cls.users_pool.create(
        cr, uid, {'name': 'Admin 0', 'login': 'user_000',
                  'password': 'user_000',
                  'groups_id': [[4, cls.admin_group_id[0]]],
                  'pos_id': cls.pos_id})

    cls.users = {'wm': [], 'ns': [], 'hc': [], 'dr': []}
    cls.locations = {}
    for i in range(iterations):

        shift_coordinator = cls.users_pool.create(
            cr, uid, {'name': 'Shift Coordinator ' + str(i),
                      'login': 'WM' + str(i),
                      'password': 'WM' + str(i),
                      'groups_id': [[4, cls.wm_group_id[0]]],
                      'pos_id': cls.pos_id}
        )
        cls.users['wm'].append(shift_coordinator)

        ward_id = cls.location_pool.create(
            cr, uid, {'name': 'Ward' + str(i), 'code': 'WARD' + str(i),
                      'usage': 'ward', 'parent_id': cls.hospital_id,
                      'type': 'poc',
                      'user_ids': [(6, 0, [shift_coordinator])]}
        )

        bed_ids = [cls.location_pool.create(
            cr, uid, {'name': 'Bed' + str(i) + str(j),
                      'code': 'BED' + str(i) + str(j), 'usage': 'bed',
                      'parent_id': ward_id, 'type': 'poc'}
        ) for j in range(10)]
        cls.locations[ward_id] = bed_ids

        cls.users['ns'].append(cls.users_pool.create(
            cr, uid, {'name': 'Nurse ' + str(i), 'login': 'NURSE' + str(i),
                      'password': 'NURSE' + str(i),
                      'groups_id': [[4, cls.nurse_group_id[0]]],
                      'pos_id': cls.pos_id})
        )

        cls.users['hc'].append(cls.users_pool.create(
            cr, uid, {'name': 'HCA ' + str(i), 'login': 'HCA' + str(i),
                      'password': 'HCA' + str(i),
                      'groups_id': [[4, cls.hca_group_id[0]]],
                      'pos_id': cls.pos_id})
        )

        cls.users['dr'].append(cls.users_pool.create(
            cr, uid, {'name': 'Doctor ' + str(i), 'login': 'DR' + str(i),
                      'password': 'DR' + str(i),
                      'groups_id': [[4, cls.doctor_group_id[0]]],
                      'pos_id': cls.pos_id,
                      'location_ids': [(6, 0, [ward_id] + bed_ids)]})
        )

    cls.patients = [cls.patient_pool.create(
        cr, uid, {'given_name': 'p' + str(k), 'family_name': 'f' + str(k),
                  'other_identifier': 'hn' + str(k)}) for k in range(5)]
