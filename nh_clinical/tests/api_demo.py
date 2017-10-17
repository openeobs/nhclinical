# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import logging

from faker import Faker
from openerp.osv import orm, osv
from openerp import SUPERUSER_ID


_logger = logging.getLogger(__name__)

fake = Faker()


class nh_clinical_api_demo(orm.AbstractModel):
    """Generates demo data for nh_clinical."""

    _name = 'nh.clinical.api.demo'

    def __init__(self, pool, cr):
        self._fake = fake
        self._seed = self._fake.random_int(min=1000001, max=9999999)
        super(nh_clinical_api_demo, self).__init__(pool, cr)

    def next_seed_fake(self, seed=None):
        if seed:
            self._fake.seed(seed)
        else:
            self._seed += 1
            self._fake.seed(self._seed)
        return self._fake

    def demo_data(self, cr, uid, model, values_method=None, values=None):
        if values is None:
            values = {}
        api_demo_data = self.pool['nh.clinical.api.demo.data']
        values_method = values_method or\
            api_demo_data._default_values_methods.get(model)
        if not values_method:
            osv.except_osv(
                'API demo error!',
                'Values method is not passed and default method is not set!')
        v = eval("api_demo_data.{method}(cr, uid, values)".format(
            method=values_method))
        return v

    def create(self, cr, uid, model, values_method=None, values=None,
               context=None):
        if values is None:
            values = {}
        model_pool = self.pool[model]
        v = self.demo_data(cr, uid, model, values_method, values)
        _logger.debug("Creating DEMO resource '%s', values: %s" % (model, v))
        res_id = model_pool.create(cr, uid, v, context)
        return res_id

    def create_activity(self, cr, uid, model, values_method=None,
                        activity_values=None, data_values=None, context=None):
        if activity_values is None:
            activity_values = {}
        if data_values is None:
            data_values = {}
        model_pool = self.pool[model]
        v = self.demo_data(cr, uid, model, values_method, data_values)
        _logger.debug("Creating DEMO resource '%s', values: %s" % (model, v))
        activity_id = model_pool.create_activity(cr, uid, activity_values, v,
                                                 context)
        return activity_id

    def demo_data_loaded(self, cr, uid):
        imd = self.pool['ir.model.data']
        ids = imd.search(cr, uid, [['name', '=', 'nhc_def_conf_pos_hospital']])
        return bool(ids)

    def create_ward(self, cr, uid, name, parent_id, code=None, bed_count=0,
                    policy_context=None, context=None):
        """
        Creates a new Ward Location
        :param name: ward name (String) - Required
        :param parent_id: id of the parent location (usually the Hospital)
        - Required
        :param code: ward code, used to reference the ward in ADT operations.
        Defaults to name if not specified. (String)
        :param bed_count: number of beds (child locations) that the ward is
        going to have. (Integer)
        :param policy_context: name of the policy the ward is going to follow.
        i.e. 'eobs' (String)
        :return: dictionary containing 'ward_id' and 'bed_ids'.
                {'ward_id': Integer, 'bed_ids': [Integers]}
        """
        location_pool = self.pool['nh.clinical.location']
        res = {'bed_ids': []}
        if policy_context:
            context_pool = self.pool['nh.clinical.context']
            context_ids = context_pool.search(cr, uid,
                                              [['name', '=', policy_context]],
                                              context=context)
        if not code:
            code = name
        res['ward_id'] = location_pool.create(cr, uid, {
            'parent_id': parent_id,
            'name': name,
            'code': code,
            'type': 'structural',
            'usage': 'ward',
            'context_ids': [[6, False, context_ids]] if policy_context
            else False
        }, context=context)
        for bed in range(bed_count):
            res['bed_ids'].append(location_pool.create(cr, uid, {
                'parent_id': res['ward_id'],
                'name': 'Bed '+str(bed),
                'code': code+'B'+str(bed),
                'type': 'structural',
                'usage': 'bed',
                'context_ids': [[6, False, context_ids]] if policy_context
                else False
            }, context=context))
        return res

    def create_user(self, cr, uid, name, login=None, password=None,
                    groups=None, location_ids=None, context=None):
        """
        Creates a new User
        :param name: name of the user (String) - Required
        :param login: login username (String)
        Defaults to name if not specified.
        :param password: user password (String)
        Defaults to login if not specified.
        :param groups: list of group names the user is going to be in.
        :type groups: list of str
        :param location_ids: list of location ids the user is responsible for.
        :type location_ids: list of int
        :return: id of the new user. (Integer)
        """
        user_pool = self.pool['res.users']
        group_pool = self.pool['res.groups']
        groups = [] if not groups else groups
        if 'NH Clinical Admin Group' in groups or\
                'NH Clinical Shift Coordinator Group' in groups:
            groups.append('Contact Creation')
        location_ids = [[6, False, []]] if not location_ids\
            else [[6, False, location_ids]]
        login = name if not login else login
        password = login if not password else password
        group_ids = group_pool.search(cr, uid, [['name', 'in', groups]],
                                      context=context)
        res = user_pool.create(cr, uid, {
            'name': name,
            'login': login,
            'groups_id': [[6, False, group_ids]],
            'location_ids': location_ids
        }, context=context)
        user_pool.write(cr, res, res, {'password': password}, context=context)
        return res

    def build_uat_env(self, cr, uid, pos=1, ward='A', wm='winifred',
                      nurse='norah', patients=8, placements=4, ews=1,
                      context=None):
        """
        Creates UAT environment in the provided ward.
        Adds patients and observations.
        """
        # pos_id is not always 1
        pos = self.pool['ir.model.data'].get_object(
            cr, uid, 'nh_eobs_default', 'nhc_def_conf_pos_hospital')
        pos = pos.id

        activity_pool = self.pool['nh.activity']
        user_pool = self.pool['res.users']
        location_pool = self.pool['nh.clinical.location']
        # CHECK PARAMETERS
        assert self.pool['nh.clinical.pos'].read(cr, uid, pos,
                                                 context=context)
        wm_exists = user_pool.search(cr, uid, [('login', '=', wm)],
                                     context=context)
        assert wm_exists
        nurse_exists = user_pool.search(cr, uid, [('login', '=', nurse)],
                                        context=context)
        assert nurse_exists
        assert self.pool['nh.clinical.location'].search(
            cr, uid, [('code', '=', ward), ('usage', '=', 'ward'),
                      ('user_ids', 'in', wm_exists)], context=context)
        assert patients > 0
        assert placements > 0
        assert patients >= placements
        adt_uid = user_pool.search(cr, uid, [('login', '=', 'adt')],
                                   context=context)[0]
        wm_uid = wm_exists[0]
        nurse_uid = nurse_exists[0]
        # GENERATE ENVIRONMENT
        admit_activity_ids = [self.create_activity(
            cr, adt_uid, 'nh.clinical.adt.patient.admit',
            data_values={'location': ward}) for i in range(patients)]
        [activity_pool.complete(cr, uid, id) for id in admit_activity_ids]
        temp_bed_ids = location_pool.search(cr, uid,
                                            [('parent_id.code', '=', ward),
                                             ('usage', '=', 'bed'),
                                             ('is_available', '=', True)],
                                            context=context)
        temp_placement_activity_ids = activity_pool.search(cr, wm_uid, [
            ['data_model', '=', 'nh.clinical.patient.placement'],
            ['state', 'in', ['new', 'scheduled']]], context=context)

        for i in range(placements):
            if not temp_bed_ids or not temp_placement_activity_ids:
                break
            placement_activity_id = fake.random_element(
                temp_placement_activity_ids)
            bed_location_id = fake.random_element(temp_bed_ids)
            activity_pool.submit(cr, wm_uid, placement_activity_id,
                                 {'location_id': bed_location_id},
                                 context=context)
            activity_pool.complete(cr, wm_uid, placement_activity_id,
                                   context=context)
            temp_placement_activity_ids.remove(placement_activity_id)
            temp_bed_ids.remove(bed_location_id)
        ews_ids = activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.patient.observation.ews'],
            ['state', 'in', ['new', 'scheduled']]], context=context)

        # EWS
        for i in range(ews):
            for ews in ews_ids:
                activity_pool.assign(cr, uid, ews, nurse_uid, context=context)
                activity_pool.submit(cr, nurse_uid, ews, self.demo_data(
                    cr, uid, 'nh.clinical.patient.observation.ews'),
                    context=context)
                activity_pool.complete(cr, nurse_uid, ews, context=context)
            ews_ids = activity_pool.search(cr, uid, [
                ['data_model', '=', 'nh.clinical.patient.observation.ews'],
                ['state', 'in', ['new', 'scheduled']]], context=context)

        return True

    def build_unit_test_env1(self, cr, uid, wards=None, bed_count=2,
                             patient_count=2, users=None):
        """
        Create a default unit test environment for basic unit tests.
            2 WARDS - U and T
            2 beds per ward - U01, U02, T01, T02
            2 patients admitted per ward
            1 patient placed in bed per ward
        The environment is customizable, the wards parameter must be a list of
        ward codes. All the other parameters are
        the number of beds, patients and placements we want.

        users parameter expects a dictionary with the following format:
            {
                'shift_coordinators': {
                    'name': ['login', 'ward_code']
                },
                'nurses': {
                    'name': ['login', [list of locations]]
                },
                'hcas': {
                    'name': ['login', [list of locations]]
                },
                'doctors': {
                    'name': ['login', [list of locations]]
                }
            }
            if there is no data the default behaviour will be to add
            a ward manager per ward i.e. 'WMU' and 'WMT' and
            a nurse responsible for all beds in the ward i.e. 'NU' and 'NT'
        """
        if not wards:
            wards = ['U', 'T']
        location_pool = self.pool['nh.clinical.location']
        pos_id = self.create(cr, uid, 'nh.clinical.pos')
        pos_location_id = location_pool.search(cr, uid,
                                               [('pos_id', '=', pos_id)])[0]

        # LOCATIONS
        ward_ids = [self.create(
            cr, uid, 'nh.clinical.location', 'location_ward',
            {'parent_id': pos_location_id, 'name': 'Ward '+w, 'code': w})
            for w in wards]
        i = 0
        bed_ids = {}
        bed_codes = {}
        for wid in ward_ids:
            bed_ids[wards[i]] = [self.create(cr, uid, 'nh.clinical.location',
                                             'location_bed',
                                             {
                                                 'parent_id': wid,
                                                 'name': 'Bed '+str(n),
                                                 'code': wards[i]+str(n)
                                             }) for n in range(bed_count)]
            bed_codes[wards[i]] = [wards[i]+str(n) for n in range(bed_count)]
            i += 1

        # USERS
        if not users:
            users = {'ward_managers': {}, 'nurses': {}}
            for w in wards:
                users['ward_managers']['WM'+w] = ['WM'+w, w]
                users['nurses']['N'+w] = ['N'+w, bed_codes[w]]

        if users.get('ward_managers'):
            wm_ids = {}
            for wm in users['ward_managers'].keys():
                wid = location_pool.search(
                    cr, uid, [('code', '=', users['ward_managers'][wm][1])])
                wm_ids[wm] = self.create(
                    cr, uid, 'res.users', 'user_ward_manager',
                    {'name': wm, 'login': users['ward_managers'][wm][0],
                     'location_ids': [[6, False, wid]]})

        if users.get('nurses'):
            n_ids = {}
            for n in users['nurses'].keys():
                lids = location_pool.search(
                    cr, uid, [('code', 'in', users['nurses'][n][1])])
                n_ids[n] = self.create(
                    cr, uid, 'res.users', 'user_nurse',
                    {'name': n, 'login': users['nurses'][n][0],
                     'location_ids': [[6, False, lids]]})

        if users.get('hcas'):
            h_ids = {}
            for h in users['hcas'].keys():
                lids = location_pool.search(
                    cr, uid, [('code', 'in', users['hcas'][h][1])])
                h_ids[h] = self.create(
                    cr, uid, 'res.users', 'user_hca',
                    {'name': h, 'login': users['hcas'][h][0],
                     'location_ids': [[6, False, lids]]})

        if users.get('doctors'):
            d_ids = {}
            for d in users['doctors'].keys():
                lids = location_pool.search(
                    cr, uid, [('code', 'in', users['doctors'][d][1])])
                d_ids[d] = self.create(
                    cr, uid, 'res.users', 'user_doctor',
                    {'name': d, 'login': users['doctors'][d][0],
                     'location_ids': [[6, False, lids]]})

        self.create(cr, uid, 'res.users', 'user_adt',
                    {'name': 'ADT', 'login': 'unittestadt', 'pos_id': pos_id})

        patient_ids = []
        for i in range(patient_count):
            patient_ids.append(self.create(cr, uid, 'nh.clinical.patient',
                                           'patient', {}))

        return patient_ids

    def get_available_bed(self, cr, uid, location_ids=None, pos_id=None):
        if location_ids is None:
            location_ids = []
        location_pool = self.pool['nh.clinical.location']
        fake = self.next_seed_fake()
        # find available in passed location_ids
        if location_ids:
            location_ids = location_pool.search(cr, uid, [
                ['id', 'in', location_ids], ['usage', '=', 'bed'],
                ['is_available', '=', True]])
            if location_ids:
                return fake.random_element(location_ids)
        # ensure pos_id is set
        if not pos_id:
            pos_ids = self.pool['nh.clinical.pos'].search(cr, uid, [])
            if pos_ids:
                pos_id = pos_ids[0]
            else:
                raise orm.except_orm(
                    'POS not found!',
                    'pos_id was not passed and existing POS is not found.')
        # try to find existing locations
        location_ids = location_pool.search(cr, uid, [
            ['id', 'in', location_ids], ['usage', '=', 'bed'],
            ['is_available', '=', True]])
        if location_ids:
            return fake.random_element(location_ids)
        # create new location
        ward_location_ids = location_pool.search(cr, uid,
                                                 [['usage', '=', 'ward'],
                                                  ['pos_id', '=', pos_id]])
        if not ward_location_ids:
            pos_location_ids = location_pool.search(
                cr, uid, [['usage', '=', 'pos'], ['pos_id', '=', pos_id]])[0]
            ward_location_id = self.create(cr, uid, 'nh.clinical.location',
                                           'location_ward',
                                           {'parent_id': pos_location_ids[0]})
        else:
            ward_location_id = fake.random_element(ward_location_ids)
        location_id = self.create(cr, uid, 'nh.clinical.location',
                                  'location_bed',
                                  {'parent_id': ward_location_id})
        return location_id

    def get_nurse(self, cr, uid):
        user_pool = self.pool['res.users']
        nurse_uid = user_pool.search(
            cr, uid, [['groups_id.name', 'in', ['NH Clinical Nurse Group']]])
        if uid in nurse_uid:
            nurse_uid = uid
        else:
            nurse_uid = nurse_uid[0] if nurse_uid else self.create(
                cr, uid, 'res.users', 'user_nurse')
        return nurse_uid

    def user_add_location(self, cr, uid, user_id, location_id):
        """
        Adds location_id to user's responsibility location list
        """
        self.pool['res.users'].write(cr, uid, user_id,
                                     {'location_ids': ([4, location_id])})
        return

    def get_adt_user(self, cr, uid, pos_id):
        """
        Returns ADT user id for pos_id
        If uid appears to be ADT user id, returns uid
        """
        user_pool = self.pool['res.users']
        adt_uid = user_pool.search(
            cr, uid, [['groups_id.name', 'in', ['NH Clinical ADT Group']]])
        if uid in adt_uid:
            adt_uid = uid
        else:
            adt_uid = adt_uid[0] if adt_uid else self.create(
                cr, uid, 'res.users', 'user_adt', {'pos_id': pos_id})
        return adt_uid

    def register_admit(self, cr, uid, pos_id, register_values=None,
                       admit_values=None, return_id=False):
        """
        Registers and admits patient to POS. Missing data will be generated
        """
        if register_values is None:
            register_values = {}
        if admit_values is None:
            admit_values = {}
        activity_pool = self.pool['nh.activity']
        # ensure pos_id is set
        if not pos_id:
            pos_ids = self.pool['nh.clinical.pos'].search(cr, uid, [])
            if pos_ids:
                pos_id = pos_ids[0]
            else:
                raise orm.except_orm(
                    'POS not found!',
                    'pos_id was not passed and existing POS is not found.')
        adt_uid = self.get_adt_user(cr, uid, pos_id)
        reg_activity_id = self.create_activity(
            cr, adt_uid, 'nh.clinical.adt.patient.register', None, {},
            register_values)
        activity_pool.complete(cr, adt_uid, reg_activity_id)
        reg_data = activity_pool.browse(cr, uid, reg_activity_id)

        admit_data = {
            'other_identifier': reg_data.data_ref.other_identifier,
        }
        admit_data.update(admit_values)
        admit_activity_id = self.create_activity(
            cr, adt_uid, 'nh.clinical.adt.patient.admit', None, {}, admit_data)
        if return_id:
            return admit_activity_id
        else:
            return activity_pool.browse(cr, uid, admit_activity_id)

    def register_admission(self, cr, uid, ward_location_id,
                           register_values=None, admit_values=None,
                           return_id=False):
        """
        Registers and admits patient to POS. Missing data will be generated
        """
        if register_values is None:
            register_values = {}
        if admit_values is None:
            admit_values = {}
        location_pool = self.pool['nh.clinical.location']
        activity_pool = self.pool['nh.activity']
        # ensure pos_id is set
        ward_location = location_pool.browse(cr, uid, ward_location_id)
        pos_id = ward_location.pos_id.id
        admit_activity = self.register_admit(
            cr, uid, pos_id, register_values,
            admit_values={'location': ward_location.code})
        activity_pool.complete(cr, uid, admit_activity.id)
        admission_activity_id = activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.patient.admission'],
            ['creator_id', '=', admit_activity.id]])[0]
        if return_id:
            return admission_activity_id
        else:
            return activity_pool.browse(cr, uid, admission_activity_id)

    def _find_ward(self, location_browse):
        if location_browse.usage == 'ward':
            return location_browse.code
        elif location_browse.parent_id:
            return self._find_ward(location_browse.parent_id)
        else:
            return False

    def register_admit_place(self, cr, uid, bed_location_id=None,
                             register_values=None, admit_values=None,
                             return_id=False):
        """
        Registers, admits and places patient into bed_location_id if vacant
        otherwise found among existing ones or created.
        Missing data will be generated
        """
        if register_values is None:
            register_values = {}
        if admit_values is None:
            admit_values = {}
        activity_pool = self.pool['nh.activity']
        location_pool = self.pool['nh.clinical.location']
        bed_location = location_pool.browse(cr, uid, bed_location_id)
        pos_id = bed_location.pos_id.id
        ward_code = self._find_ward(bed_location)
        if ward_code:
            admit_values['location'] = ward_code
        admit_activity = self.register_admit(cr, uid, pos_id, register_values,
                                             admit_values)
        activity_pool.complete(cr, uid, admit_activity.id)
        admission_activity_id = activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.patient.admission'],
            ['creator_id', '=', admit_activity.id]])[0]
        placement_activity_id = activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.patient.placement'],
            ['creator_id', '=', admission_activity_id]])[0]

        activity_pool.submit(cr, uid, placement_activity_id,
                             {'location_id': bed_location_id})
        activity_pool.complete(cr, uid, placement_activity_id)
        if return_id:
            return placement_activity_id
        else:
            return activity_pool.browse(cr, uid, placement_activity_id)

    def submit_ews_observations(self, cr, uid, bed_codes=None, ews_count=3):
        if bed_codes is None:
            bed_codes = []
        location_pool = self.pool['nh.clinical.location']
        activity_pool = self.pool['nh.activity']
        user_pool = self.pool['res.users']
        imd_pool = self.pool['ir.model.data']
        imd_ids = imd_pool.search(cr, uid, [['model', '=', 'nh.clinical.pos'],
                                            ['name', 'ilike', '%hospital%']])
        pos = imd_pool.read(cr, uid, imd_ids, ['res_id'])
        if not pos:
            _logger.warning("POS hospital is not found. Exiting...")
            exit(1)
        pos_id = pos[0]['res_id']
        if not bed_codes:
            bed_ids = location_pool.search(cr, uid, [['pos_id', '=', pos_id],
                                                     ['usage', '=', 'bed']])
        else:
            bed_ids = location_pool.search(cr, uid,
                                           [['code', 'in', bed_codes]])
        beds = location_pool.browse(cr, uid, bed_ids)
        # setting up admin as a nurse
        imd_ids = imd_pool.search(cr, uid, [['model', '=', 'res.groups'],
                                            ['name', '=', 'group_nhc_nurse']])
        nurse_group_id = imd_pool.read(cr, uid, imd_ids[0],
                                       ['res_id'])['res_id']
        user_pool.write(cr, uid, SUPERUSER_ID,
                        {'groups_id': [(4, nurse_group_id)]})
        nurse_uid = SUPERUSER_ID
        for bed in beds:
            if not bed.patient_ids:
                # Patient is not placed into bed. Skipping...
                continue
            else:
                patient_id = bed.patient_ids[0]
                ews_ids = activity_pool.search(cr, uid, [
                    ['data_model', '=', 'nh.clinical.patient.observation.ews'],
                    ['patient_id', '=', patient_id],
                    ['state', 'in', ['new', 'scheduled']]])

                for i in range(ews_count):
                    for ews in ews_ids:
                        activity_pool.assign(cr, uid, ews, nurse_uid)
                        activity_pool.submit(
                            cr, nurse_uid, ews, self.demo_data(
                                cr, uid,
                                'nh.clinical.patient.observation.ews'))
                        activity_pool.complete(cr, nurse_uid, ews)
                    ews_ids = activity_pool.search(cr, uid, [
                        ['data_model',
                         '=',
                         'nh.clinical.patient.observation.ews'],
                        ['patient_id', '=', patient_id],
                        ['state', 'in', ['new', 'scheduled']]])
        user_pool.write(cr, uid, SUPERUSER_ID,
                        {'groups_id': [(3, nurse_group_id)]})
        return True


class nh_clinical_api_demo_data(orm.AbstractModel):
    _name = 'nh.clinical.api.demo.data'

    _default_values_methods = {
        'res.users': 'user_nurse',
        'nh.clinical.location': 'location_bed',
        'nh.clinical.patient': 'patient',
        'nh.clinical.pos': 'pos',
        'nh.clinical.device': 'device',
        'nh.clinical.device.type': 'device_type',

        'nh.clinical.adt.patient.register': 'adt_register',
        'nh.clinical.adt.patient.admit': 'adt_admit',
        'nh.clinical.adt.patient.discharge': 'adt_discharge',

        'nh.clinical.patient.observation.ews': 'observation_ews',
        'nh.clinical.patient.observation.height': 'observation_height',
        'nh.clinical.patient.diabetes': 'diabetes',

    }

    def __init__(self, pool, cr):
        self._fake = fake
        self._seed = self._fake.random_int(min=1000001, max=9999999)
        super(nh_clinical_api_demo_data, self).__init__(pool, cr)

    def next_seed_fake(self, seed=None):
        if seed:
            self._fake.seed(seed)
        else:
            self._seed += 1
            self._fake.seed(self._seed)
        return self._fake

# -############ base ##############-

    # -##### res.users #####-
    def _user_base(self, cr, uid, values=None):
        if values is None:
            values = {}
        fake = self.next_seed_fake()
        i = 0
        login = (values.get('name') or fake.first_name()).lower()
        while i <= 1000:
            if self.pool['res.users'].search(cr, uid, [('login', '=', login)]):
                login = fake.first_name().lower()
                i += 1
            else:
                break
        if i > 1000:
            raise orm.except_orm(
                "Demo data exception!",
                "Failed to generate unique user login after 1000 attempts!")
        v = {
            'name': login.capitalize(),
            'login': login,
            'password': login,
        }
        return v

    def user_hca(self, cr, uid, values=None):
        if values is None:
            values = {}
        imd_pool = self.pool['ir.model.data']
        group = imd_pool.get_object(cr, uid, "nh_clinical", "group_nhc_hca")
        v = self._user_base(cr, uid)
        v.update({'groups_id': [(4, group.id)]})
        v.update(values)
        return v

    def user_nurse(self, cr, uid, values=None):
        if values is None:
            values = {}
        imd_pool = self.pool['ir.model.data']
        group = imd_pool.get_object(cr, uid, "nh_clinical", "group_nhc_nurse")
        v = self._user_base(cr, uid)
        v.update({'groups_id': [(4, group.id)]})
        v.update(values)
        return v

    def user_ward_manager(self, cr, uid, values=None):
        if values is None:
            values = {}
        imd_pool = self.pool['ir.model.data']
        group = imd_pool.get_object(cr, uid, "nh_clinical",
                                    "group_nhc_ward_manager")
        v = self._user_base(cr, uid)
        v.update({'groups_id': [(4, group.id)]})
        v.update(values)
        return v

    def user_receptionist(self, cr, uid, values=None):
        if values is None:
            values = {}
        imd_pool = self.pool['ir.model.data']
        group = imd_pool.get_object(cr, uid, "nh_clinical",
                                    "group_nhc_receptionist")
        v = self._user_base(cr, uid)
        v.update({'groups_id': [(4, group.id)]})
        v.update(values)
        return v

    def user_junior_doctor(self, cr, uid, values=None):
        if values is None:
            values = {}
        imd_pool = self.pool['ir.model.data']
        group = imd_pool.get_object(cr, uid, "nh_clinical",
                                    "group_nhc_junior_doctor")
        v = self._user_base(cr, uid)
        v.update({'groups_id': [(4, group.id)]})
        v.update(values)
        return v

    def user_registrar(self, cr, uid, values=None):
        if values is None:
            values = {}
        imd_pool = self.pool['ir.model.data']
        group = imd_pool.get_object(cr, uid, "nh_clinical",
                                    "group_nhc_registrar")
        v = self._user_base(cr, uid)
        v.update({'groups_id': [(4, group.id)]})
        v.update(values)
        return v

    def user_consultant(self, cr, uid, values=None):
        if values is None:
            values = {}
        imd_pool = self.pool['ir.model.data']
        group = imd_pool.get_object(cr, uid, "nh_clinical",
                                    "group_nhc_consultant")
        v = self._user_base(cr, uid)
        v.update({'groups_id': [(4, group.id)]})
        v.update(values)
        return v

    def user_doctor(self, cr, uid, values=None):
        if values is None:
            values = {}
        imd_pool = self.pool['ir.model.data']
        group = imd_pool.get_object(cr, uid, "nh_clinical",
                                    "group_nhc_doctor")
        v = self._user_base(cr, uid)
        v.update({'groups_id': [(4, group.id)]})
        v.update(values)
        return v

    def user_adt(self, cr, uid, values=None):
        if values is None:
            values = {}
        imd_pool = self.pool['ir.model.data']
        group = imd_pool.get_object(cr, uid, "nh_clinical",
                                    "group_nhc_adt")
        v = self._user_base(cr, uid)
        v.update({'groups_id': [(4, group.id)]})
        if 'pos_id' not in values:
            api_demo = self.pool['nh.clinical.api.demo']
            v.update({'pos_id': api_demo.create(cr, uid,
                                                'nh.clinical.pos')})

        v.update(values)
        return v

    # -#### location ####-

    def location_pos(self, cr, uid, values=None):
        if values is None:
            values = {}
        fake = self.next_seed_fake()
        code = "POS_"+str(fake.random_int(min=100, max=999))
        v = {
            'name': "POS Location (%s)" % code,
            'code': code,
            'type': 'structural',
            'usage': 'hospital',
        }
        v.update(values)
        return v

    def location_discharge(self, cr, uid, values=None):
        if values is None:
            values = {}
        fake = self.next_seed_fake()
        code = "DISCHARGE_"+str(fake.random_int(min=100, max=999))
        v = {
            'name': "Discharge Location (%s)" % code,
            'code': code,
            'type': 'structural',
            'usage': 'room',
        }
        v.update(values)
        return v

    def location_admission(self, cr, uid, values=None):
        if values is None:
            values = {}
        fake = self.next_seed_fake()
        code = "ADMISSION_"+str(fake.random_int(min=100, max=999))
        v = {
            'name': "Admission Location (%s)" % code,
            'code': code,
            'type': 'structural',
            'usage': 'room',
        }
        v.update(values)
        return v

    def location_ward(self, cr, uid, values=None):
        if values is None:
            values = {}
        fake = self.next_seed_fake()
        code = "ward_"+str(fake.random_int(min=100, max=999))
        v = {
            'name': code,
            'code': code,
            'type': 'structural',
            'usage': 'ward',
        }
        v.update(values)
        return v

    def location_bed(self, cr, uid, values=None):
        if values is None:
            values = {}
        fake = self.next_seed_fake()
        code = "bed_"+str(fake.random_int(min=100, max=999))
        v = {
            'name': code,
            'code': code,
            'type': 'poc',
            'usage': 'bed',
        }
        v.update(values)
        return v

    # -#### patient ####-
    def patient(self, cr, uid, values=None):
        if values is None:
            values = {}
        fake = self.next_seed_fake()
        name = fake.first_name()
        last_name = fake.last_name(),
        gender = fake.random_element(('M', 'F'))
        v = {
            'name': name,
            'given_name': name,
            'family_name': last_name,
            'patient_identifier': "PI_"+str(fake.random_int(min=200000,
                                                            max=299999)),
            'other_identifier': "OI_"+str(fake.random_int(min=100000,
                                                          max=199999)),
            'dob': fake.date_time_between(
                start_date="-80y",
                end_date="-10y").strftime("%Y-%m-%d %H:%M:%S"),
            'gender': gender,
            'sex': gender,
        }
        v.update(values)
        return v

    # -#### pos ####-
    def pos(self, cr, uid, values=None):
        if values is None:
            values = {}
        fake = self.next_seed_fake()
        api_demo = self.pool['nh.clinical.api.demo']
        v = {'name': "(POS) HOSPITAL_"+str(fake.random_int(min=100, max=999))}
        if 'location_id' not in values:
            v.update({'location_id': api_demo.create(
                cr, uid, 'nh.clinical.location', 'location_pos')})
        if 'lot_admission_id' not in values:
            v.update({'lot_admission_id': api_demo.create(
                cr, uid, 'nh.clinical.location', 'location_admission')})
        if 'lot_discharge_id' not in values:
            v.update({'lot_discharge_id': api_demo.create(
                cr, uid, 'nh.clinical.location', 'location_discharge')})

        v.update(values)
        return v

    # -#### device.category ####-
    def device_category(self, cr, uid, values=None):
        if values is None:
            values = {}
        fake = self.next_seed_fake()
        flow_directions = dict(
            self.pool['nh.clinical.device.category']._columns[
                'flow_direction'].selection).keys()
        v = {
            'name': "DEVICE_CATEGORY_"+str(fake.random_int(min=100, max=999)),
            'flow_direction': fake.random_element(flow_directions),
        }
        return v

    # -#### device.type ####-
    def device_type(self, cr, uid, values=None):
        if values is None:
            values = {}
        fake = self.next_seed_fake()
        if 'category_id' not in values:
            category_id = fake.random_element(
                self.pool['nh.clinical.device.category'].search(cr, uid, []))
            if not category_id:
                api_demo = self.pool['nh.clinical.api.demo']
                category_id = api_demo.create(cr, uid,
                                              'nh.clinical.device.category')
        else:
            category_id = values['category_id']
        v = {
            'name': "DEVICE_TYPE_"+str(fake.random_int(min=100, max=999)),
            'category_id': category_id,
        }
        return v

    # -#### device ####-
    def device(self, cr, uid, values=None):
        if values is None:
            values = {}
        fake = self.next_seed_fake()
        if 'type_id' not in values:
            type_id = fake.random_element(
                self.pool['nh.clinical.device.type'].search(cr, uid, []))
            if not type_id:
                api_demo = self.pool['nh.clinical.api.demo']
                type_id = api_demo.create(cr, uid, 'nh.clinical.device.type')
        else:
            type_id = values['type_id']
        v = {
            'serial_number': "DEVICE_"+str(fake.random_int(min=1000,
                                                           max=9999)),
            'type_id': type_id
        }
        v.update(values)
        return v

# -######### activity types ###########-
    def adt_register(self, cr, uid, values=None):
        if values is None:
            values = {}
        fake = self.next_seed_fake()
        gender = fake.random_element(['M', 'F'])
        v = {
            'family_name': fake.last_name(),
            'given_name': fake.first_name(),
            'other_identifier': str(fake.random_int(min=1000001, max=9999999)),
            'patient_identifier': str(fake.random_int(min=1000000000,
                                                      max=9999999999)),
            'dob': fake.date_time_between(
                start_date="-80y",
                end_date="-10y").strftime("%Y-%m-%d %H:%M:%S"),
            'gender': gender,
            'sex': gender,
        }
        v.update(values)
        return v

    def adt_admit(self, cr, uid, values=None):
        if values is None:
            values = {}
        fake = self.next_seed_fake()
        api_demo = self.pool['nh.clinical.api.demo']
        activity_pool = self.pool['nh.activity']
        location_pool = self.pool['nh.clinical.location']
        user_pool = self.pool['res.users']
        user = user_pool.browse(cr, uid, uid)
        v = {}
        # If 'other_identifier' is not passed, then register a new patient
        # and use it's data.
        pos_id = 'pos_id' in values and values.pop('pos_id') or False
        if 'other_identifier' not in values:
            reg_activity_id = api_demo.create_activity(
                cr, uid, 'nh.clinical.adt.patient.register')
            activity_pool.complete(cr, uid, reg_activity_id)
            reg_data = activity_pool.browse(cr, uid, reg_activity_id)
            v.update({'other_identifier': reg_data.data_ref.other_identifier})
            pos_id = reg_data.data_ref.pos_id.id
        if 'location' not in values:
            ward_ids = location_pool.search(cr, uid, [['pos_id', '=', pos_id],
                                                      ['usage', '=', 'ward']])
            if not ward_ids:
                pos = self.pool['nh.clinical.pos'].browse(cr, uid,
                                                          user.pos_id.id)
                ward_location_id = api_demo.create(
                    cr, uid, 'nh.clinical.location', 'location_ward',
                    {'parent_id': pos.location_id.id})
                ward_ids = [ward_location_id]
            ward_id = fake.random_element(ward_ids)
            ward = location_pool.browse(cr, uid, ward_id)
            v.update({'location': ward.code})
        v.update(values)
        return v

    def adt_discharge(self, cr, uid, values=None):
        if values is None:
            values = {}
        fake = self.next_seed_fake()
        activity_pool = self.pool['nh.activity']
        patient_pool = self.pool['nh.clinical.patient']
        spell_ids = activity_pool.search(
            cr, uid, [['data_model', '=', 'nh.clinical.spell'],
                      ['state', '=', 'started']])
        patient_ids = [s.patient_id.id for s in activity_pool.browse(
            cr, uid, spell_ids)]
        patient = fake.random_element(patient_pool.browse(cr, uid,
                                                          patient_ids))
        v = {
            'other_identifier': patient.other_identifier,
        }
        v.update(values)
        return v

    def observation_ews(self, cr, uid, values=None):
        if values is None:
            values = {}
        fake = self.next_seed_fake()
        # pos_id = 'pos_id' in values and values.pop('pos_id') or False

        respiration_rate = [fake.random_int(min=12, max=20)]*900 +\
                           [fake.random_int(min=9, max=11)]*50 +\
                           [fake.random_int(min=21, max=24)]*40 +\
                           [fake.random_int(min=6, max=8)]*5 +\
                           [fake.random_int(min=25, max=28)]*5
        o2 = [fake.random_int(min=96, max=100)]*900 +\
             [fake.random_int(min=94, max=95)]*50 +\
             [fake.random_int(min=92, max=93)]*40 +\
             [fake.random_int(min=75, max=91)]*10
        o2_flag = [0]*800+[1]*200
        bt = [fake.random_int(min=361, max=380)]*900 +\
             [fake.random_int(min=351, max=360)]*25 +\
             [fake.random_int(min=381, max=390)]*25 +\
             [fake.random_int(min=391, max=420)]*40 +\
             [fake.random_int(min=340, max=350)]*10
        bps = fake.random_element([fake.random_int(min=111, max=219)]*900 +
                                  [fake.random_int(min=101, max=110)]*50 +
                                  [fake.random_int(min=91, max=100)]*40 +
                                  [fake.random_int(min=85, max=90)]*5 +
                                  [fake.random_int(min=220, max=225)]*5)
        pr = [fake.random_int(min=51, max=90)]*900 +\
             [fake.random_int(min=41, max=50)]*25 +\
             [fake.random_int(min=91, max=110)]*25 +\
             [fake.random_int(min=111, max=130)]*40 +\
             [fake.random_int(min=20, max=40)]*5 +\
             [fake.random_int(min=131, max=150)]*5
        avpu = ['A']*850+['V']*50+['P']*50+['U']*50
        v = {
            'respiration_rate': fake.random_element(respiration_rate),
            'indirect_oxymetry_spo2': fake.random_element(o2),
            'body_temperature': float(fake.random_element(bt))/10.0,
            'blood_pressure_systolic': bps,
            'pulse_rate': fake.random_element(pr),
            'avpu_text': fake.random_element(avpu),
            'oxygen_administration_flag': fake.random_element(o2_flag),
            'blood_pressure_diastolic': bps-fake.random_int(min=10, max=45),
        }
        v.update(values)  # in case the flag passed in values
        if v['oxygen_administration_flag']:
            v.update({
                'flow_rate': fake.random_int(min=40, max=60),
                'concentration': fake.random_int(min=50, max=100),
                'cpap_peep': fake.random_int(min=1, max=100),
                'niv_backup': fake.random_int(min=1, max=100),
                'niv_ipap': fake.random_int(min=1, max=100),
                'niv_epap': fake.random_int(min=1, max=100),
            })
#         if not d['patient_id']:
#             _logger.warn("No patients available for ews!")
        v.update(values)
        return v

    def observation_height(self, cr, uid, values=None):
        if values is None:
            values = {}
        fake = self.next_seed_fake()
        v = {}
        assert 'patient_id' in values, "'patient_id' is not in values!"
        v.update({'height': float(fake.random_int(min=120, max=220))})
        v.update(values)
        return v

    def diabetes(self, cr, uid, values=None):
        if values is None:
            values = {}
        fake = self.next_seed_fake()
        v = {}
        assert 'patient_id' in values, "'patient_id' is not in values!"
        v.update({'diabetes': fake.random_element([True, False])})
        v.update(values)
        return v
