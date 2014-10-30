from openerp.tests import common
from datetime import datetime as dt
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf

import logging
_logger = logging.getLogger(__name__)

from faker import Faker
fake = Faker()
seed = fake.random_int(min=0, max=9999999)


def next_seed():
    global seed
    seed += 1
    return seed


class TestInternalAPI(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestInternalAPI, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.users_pool = cls.registry('res.users')
        cls.groups_pool = cls.registry('res.groups')
        cls.partner_pool = cls.registry('res.partner')
        cls.activity_pool = cls.registry('nh.activity')
        cls.patient_pool = cls.registry('nh.clinical.patient')
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.spell_pool = cls.registry('nh.clinical.spell')
        cls.api_pool = cls.registry('nh.clinical.api')

        cls.apidemo = cls.registry('nh.clinical.api.demo')

        cls.apidemo.build_unit_test_env(cr, uid, bed_count=4, patient_count=4)

        cls.wu_id = cls.location_pool.search(cr, uid, [('code', '=', 'U')])[0]
        cls.wt_id = cls.location_pool.search(cr, uid, [('code', '=', 'T')])[0]
        cls.pos_id = cls.location_pool.read(cr, uid, cls.wu_id, ['pos_id'])['pos_id'][0]
        cls.pos_location_id = cls.pos_pool.read(cr, uid, cls.pos_id, ['location_id'])['location_id'][0]

        cls.wmu_id = cls.users_pool.search(cr, uid, [('login', '=', 'WMU')])[0]
        cls.wmt_id = cls.users_pool.search(cr, uid, [('login', '=', 'WMT')])[0]
        cls.nu_id = cls.users_pool.search(cr, uid, [('login', '=', 'NU')])[0]
        cls.nt_id = cls.users_pool.search(cr, uid, [('login', '=', 'NT')])[0]
        cls.adt_id = cls.users_pool.search(cr, uid, [('groups_id.name', 'in', ['NH Clinical ADT Group']), ('pos_id', '=', cls.pos_id)])[0]

        patient_ids = cls.patient_pool.search(cr, uid, [])
        patient_id = fake.random_element(patient_ids)
        patient2_id = fake.random_element(patient_ids)
        while patient2_id == patient_id:
            patient2_id = fake.random_element(patient_ids)
        code = str(fake.random_int(min=1000001, max=9999999))
        code2 = str(fake.random_int(min=100001, max=999999))
        spell_data = {
            'patient_id': patient_id,
            'pos_id': cls.pos_id,
            'code': code,
            'start_date': dt.now().strftime(dtf)}
        spell2_data = {
            'patient_id': patient2_id,
            'pos_id': cls.pos_id,
            'code': code2,
            'start_date': dt.now().strftime(dtf)}
        spell_activity_id = cls.spell_pool.create_activity(cr, uid, {}, spell_data)
        cls.activity_pool.start(cr, uid, spell_activity_id)
        spell_activity_id = cls.spell_pool.create_activity(cr, uid, {}, spell2_data)
        cls.activity_pool.start(cr, uid, spell_activity_id)

    def test_api_location_map(self):
        cr, uid = self.cr, self.uid

        # get patients
        spell_activities = self.api_pool.get_activities(cr, uid, data_models=['nh.clinical.spell'], states=['started'], pos_ids=[self.pos_id])
        self.assertTrue(len(spell_activities) == 2, msg="API get_activities did not find the correct number of spells")
        patients = [a.patient_id for a in spell_activities]
        bed_locations = self.api_pool.get_locations(cr, uid, pos_ids=[self.pos_id], usages=['bed'])
        self.assertTrue(len(bed_locations) == 8, msg="API get_locations did not find the correct number of beds")
        amap = self.api_pool.location_map(cr, uid, usages=['bed'], available_range=[0, 1], pos_ids=[self.pos_id])
        available_ids = [k for k, v in amap.items() if amap[k]['available'] > 0]
        unavailable_ids = list(set(amap.keys()) - set(available_ids))
        self.assertTrue(len(unavailable_ids) == 0, msg="API location_map did not retrieve location data correctly: unavailable beds")
        self.assertTrue(len(available_ids) == 8, msg="API location_map did not retrieve location data correctly: available beds")
        # test moves 0->1->2->3 ....
        for i in range(len(available_ids)):
            patient_id = patients[0].id
            location_id = available_ids[i]
            move = self.api_pool.create_complete(cr, uid, 'nh.clinical.patient.move', {}, {'patient_id': patient_id, 'location_id': location_id})
            # availability
            amap = self.api_pool.location_map(cr, uid, usages=['bed'], available_range=[0, 1], pos_ids=[self.pos_id])
            self.assertFalse(amap[available_ids[i]]['available'], msg="API create_complete Patient Move: Location availability not updated correctly")
            if i > 0:
                self.assertTrue(amap[available_ids[i-1]]['available'], msg="API create_complete Patient Move: Location availability incorrect")
            # patient
            amap = self.api_pool.location_map(cr, uid, usages=['bed'], patient_ids=[patient_id], available_range=[0, 1], pos_ids=[self.pos_id])
            self.assertTrue(len(amap) == 1, msg="API create_complete Patient Move: Patient found in more than one location")
            self.assertTrue(len(amap[location_id]['patient_ids']) == 1, msg="API create_complete Patient Move: More patients returned than expected")
            self.assertTrue(amap[location_id]['patient_ids'][0] == patient_id, msg="API create_complete Patient Move: Wrong patient returned")
            amap = self.api_pool.location_map(cr, uid, usages=['bed'], patient_ids=[patient_id], available_range=[0, 1], pos_ids=[self.pos_id])

    def test_api_patient_map(self):
        cr, uid = self.cr, self.uid
        patient_ids = self.patient_pool.search(cr, uid, [])
        self.patient_pool.write(cr, uid, patient_ids, {'current_location_id': self.pos_location_id})
        patients = self.api_pool.patient_map(cr, uid, location_ids=[self.pos_location_id])
        self.assertTrue(len(patients) == 4, msg="API patient_map did not find patients by Location ID")
        self.patient_pool.write(cr, uid, patient_ids, {'current_location_id': self.wu_id})
        patients = self.api_pool.patient_map(cr, uid, parent_location_ids=[self.pos_location_id])
        self.assertTrue(len(patients) == 4, msg="API patient_map did not find patients by Parent Location ID")
        # patients = self.api_pool.patient_map(cr, uid, pos_ids=[self.pos_id])
        # self.assertTrue(len(patients) == 4, msg="API patient_map did not find patients by POS ID") --> currently not working properly if there is no patient move activity
        patients = self.api_pool.patient_map(cr, uid, patient_ids=patient_ids)
        self.assertTrue(len(patients) == 4, msg="API patient_map did not find patients by Patient ID")
        patients = self.api_pool.patient_map(cr, uid, patient_ids=patient_ids,
                                            parent_location_ids=[self.pos_location_id],
                                            location_ids=[self.wu_id])
        self.assertTrue(len(patients) == 4, msg="API patient_map combined search failed")

    def test_api_user_map(self):
        cr, uid = self.cr, self.uid
        # test group_xmlids
        umap = self.api_pool.user_map(cr, uid, group_xmlids=['group_nhc_ward_manager'])
        self.assertTrue(self.wmu_id in umap.keys() and self.wmt_id in umap.keys(), msg="API user_map did not find users by Group XML ID")
        umap = self.api_pool.user_map(cr, uid, group_xmlids=['group_nhc_adt'])
        self.assertTrue(self.adt_id in umap.keys(), msg="API user_map did not find users by Group XML ID")
        umap = self.api_pool.user_map(cr, uid, group_xmlids=['group_nhc_nurse'])
        self.assertTrue(self.nu_id in umap.keys() and self.nt_id in umap.keys(), msg="API user_map did not find users by Group XML ID")
        # test assigned_activity_ids
        activities = self.api_pool.get_activities(cr, uid, pos_ids=[self.pos_id], data_models=['nh.clinical.spell'])
        activity_ids = [a.id for a in activities]
        [self.api_pool.assign(cr, uid, activity_id, self.nu_id) for activity_id in activity_ids]
        umap = self.api_pool.user_map(cr, uid, assigned_activity_ids=activity_ids)
        self.assertTrue(self.nu_id in umap.keys(), msg="API user_map did not find users by Assigned Activities")

    def test_api_activity_map(self):
        cr, uid = self.cr, self.uid

        args = {
            'pos_ids': [self.pos_id],
            'data_models': ['nh.clinical.spell'],
            'patient_ids': self.patient_pool.search(cr, uid, []),
            'location_ids': self.location_pool.search(cr, uid, [['parent_id', '=', self.pos_location_id]]),
            'states': ['started', 'completed', 'scheduled'],
        }
        for i in range(len(args)*10):
            keys = [fake.random_element(args.keys()) for j in range(fake.random_int(1, len(args)-1))]
            kwargs = {k: args[k] for k in keys}
            domain = [[k[:-1], 'in', args[k]] for k in keys]
            activity_map = self.api_pool.activity_map(cr, uid, **kwargs)
            activity_ids = self.activity_pool.search(cr, uid, domain)
            self.assertTrue(len(activity_map) == len(activity_ids), msg="API activity_map failed")
            self.assertTrue(set(activity_map.keys()) == set(activity_ids), msg="API activity_map failed")