from openerp.tests import common
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta as rd
from openerp import tools
from openerp.tools import config
from openerp.osv import orm, fields, osv
from pprint import pprint as pp
from openerp import SUPERUSER_ID
import logging
from pprint import pprint as pp
from openerp.addons.nh_activity.activity import except_if
_logger = logging.getLogger(__name__)

from faker import Faker
fake = Faker()
seed = fake.random_int(min=0, max=9999999)


def next_seed():
    global seed
    seed += 1
    return seed


class nh_clinical_demo_env(orm.Model):
    _name = 'nh.clinical.demo.env'
    
    _columns = {
        'bed_qty': fields.integer('Bed Qty'),
        'ward_qty': fields.integer('Ward Qty'),
        'adt_user_qty': fields.integer('ADT User Qty'),
        'nurse_user_qty': fields.integer('Nurse User Qty'), 
        'ward_manager_user_qty': fields.integer('Ward Manager User Qty'),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS'),
        'patient_qty': fields.integer('Patients Qty'),  
        
    }
    _defaults = {
         'bed_qty': 3,
         'ward_qty': 2,
         'adt_user_qty': 1,
         'nurse_user_qty': 2,
         'ward_manager_user_qty': 2,
         'patient_qty': 2,
    }
    
    def data_unique_login(self, cr, uid, initial_login=None):
        fake.seed(next_seed())
        login = initial_login or fake.first_name().lower()
        sql = "select 1 from res_users where login='%s'"
        cr.execute(sql % login) 
        i = 0
        while cr.fetchone():
            i += 1
            login = fake.first_name().lower() 
            cr.execute(sql % login)
            except_if(i > 100, msg="Can't get unique login after 100 iterations!")
        return login
    
    def fake_data(self, cr, uid, env_id, model, data={}):
        """
        This method returns fake data for model
        Extend this method to add fake data for other models 
        """
        data_copy = data.copy()
        method_map = {
            # Base      
            'nh.clinical.location.bed': 'data_location_bed',
            'nh.clinical.location.ward': 'data_location_ward',
            'nh.clinical.location.pos': 'data_location_pos',
            'nh.clinical.location.admission': 'data_location_admission',
            'nh.clinical.location.discharge': 'data_location_discharge',
            'nh.clinical.pos': 'data_pos',
            # Observations
            'nh.clinical.patient.observation.ews': 'data_observation_ews',
            'nh.clinical.patient.observation.gcs': 'data_observation_gcs',
            'nh.clinical.patient.observation.height': 'data_observation_height',
            'nh.clinical.patient.observation.weight': 'data_observation_weight',
            'nh.clinical.patient.observation.blood_sugar': 'data_observation_blood_sugar',
            'nh.clinical.patient.observation.blood_product': 'data_observation_blood_product',
            'nh.clinical.patient.observation.stools': 'data_observation_stools',
            
            # ADT
            'nh.clinical.adt.patient.register': 'data_adt_patient_register',
            'nh.clinical.adt.patient.admit': 'data_adt_patient_admit',
            'nh.clinical.adt.patient.cancel_admit': 'data_adt_patient_cancel_admit',
            
            # Operations
            'nh.clinical.patient.placement': 'data_placement',              
        }
        res = None
        if method_map.get(model) and hasattr(nh_clinical_demo_env, method_map[model]):
            res = eval("self.%s(cr, uid, env_id, data=data_copy)" % method_map[model])  
        except_if(not res, msg="Data method is not defined for model '%s'" % model)
        return res
    
    def data_location_bed(self, cr, uid, env_id, data={}):
        fake.seed(next_seed())
        env = self.browse(cr, SUPERUSER_ID, env_id) 
        api_pool = self.pool['nh.clinical.api']
        locations = api_pool.get_locations(cr, uid, pos_ids=[env.pos_id.id], usages=['ward'])
        if not locations:
            _logger.warn("No ward locations found. Beds will remain without parent location!")
        code = "BED_"+str(fake.random_int(min=1000, max=9999))
        d = {
               'name': code,
               'code': code,
               'type': 'poc',
               'usage': 'bed',
               'parent_id': locations and fake.random_element(locations).id or False
        }        
        d.update(data)        
        return d

    def data_location_ward(self, cr, uid, env_id, data={}):
        fake.seed(next_seed())
        env = self.browse(cr, SUPERUSER_ID, env_id) 
        code = "WARD_"+str(fake.random_int(min=100, max=999))
        d = {
               'name': code,
               'code': code,
               'type': 'structural',
               'usage': 'ward',
               'parent_id': env.pos_id.location_id.id
        }       
        d.update(data)        
        return d        
        
    def data_location_pos(self, cr, uid, env_id, data={}):
        fake.seed(next_seed())        
        code = "POS_"+str(fake.random_int(min=100, max=999))
        d = {
               'name': "POS Location (%s)" % code,
               'code': code,
               'type': 'structural',
               'usage': 'hospital',
               }        
        d.update(data)
        return d

    def data_location_admission(self, cr, uid, env_id, data={}):
        fake.seed(next_seed())        
        code = "ADMISSION_"+str(fake.random_int(min=100, max=999))
        d = {
               'name': code,
               'code': code,
               'type': 'structural',
               'usage': 'room',
               }        
        d.update(data)
        return d

    def data_location_discharge(self, cr, uid, env_id, data={}):
        fake.seed(next_seed())        
        code = "DISCHARGE_"+str(fake.random_int(min=100, max=999))
        d = {
               'name': code,
               'code': code,
               'type': 'structural',
               'usage': 'room',
               }        
        d.update(data)
        return d

    def data_pos(self, cr, uid, env_id, data={}):
        fake.seed(next_seed())        
        d = {
                'name': "HOSPITAL_"+str(fake.random_int(min=100, max=999)),
            }         
        d.update(data)
        return d
        
    def create_activity(self, cr, uid, env_id, data_model, activity_vals={}, data_vals={}, no_fake=False, return_id=False):
        activity_pool = self.pool['nh.activity']
        data_pool = self.pool[data_model]
        if not no_fake:
            dvals = self.fake_data(cr, uid, env_id, data_model, data_vals)
        else:
            dvals = data_vals.copy()        
        activity_id = data_pool.create_activity(cr, uid, activity_vals, dvals)     
        if return_id:
            return activity_id
        else:   
            return activity_pool.browse(cr, uid, activity_id)
    
    def create_complete(self, cr, uid, env_id, data_model, activity_vals={}, data_vals={}, no_fake=False, return_id=False):
        _logger.debug("activity_vals before fake: %s" %  activity_vals)
        _logger.debug("dvals before fake: %s" %  data_vals)
        _logger.debug("create_complete.data_model: %s" % data_model)
        if not no_fake:
            dvals = self.fake_data(cr, uid, env_id, data_model, data_vals)
        else:
            dvals = data_vals.copy()
        data_pool = self.pool[data_model]
        activity_pool = self.pool['nh.activity']
        _logger.debug("activity_vals: %s" %  activity_vals)
        _logger.debug("dvals: %s" %  dvals)
        
        activity_id = data_pool.create_activity(cr, uid, activity_vals, dvals)
        activity_pool.complete(cr, uid, activity_id)       
        if return_id:
            return activity_id
        else:   
            return activity_pool.browse(cr, uid, activity_id)

    def complete(self, cr, uid, env_id, activity_id, return_id=False):  
        assert activity_id
        activity_pool = self.pool['nh.activity']
        activity_pool.complete(cr, uid, activity_id)
        if return_id:
            return activity_id
        else:   
            return activity_pool.browse(cr, uid, activity_id)
    
    def submit_complete(self, cr, uid, env_id, activity_id, data_vals={}, no_fake=False, return_id=False):  
        assert activity_id
        activity_pool = self.pool['nh.activity']
        vals = self.pool['nh.clinical.api'].get_activity_data(cr, uid, activity_id)
        vals = {k: v for k, v in vals.items() if v}
        vals.update(data_vals)
        if not no_fake:
            activity = activity_pool.browse(cr, uid, activity_id)
            vals = self.fake_data(cr, uid, env_id, activity.data_model, vals)
        activity_pool.submit(cr, uid, activity_id, vals)
        activity_pool.complete(cr, uid, activity_id)
        if return_id:
            return activity_id
        else:   
            return activity_pool.browse(cr, uid, activity_id)
    
#     def create(self, cr, uid, vals={},context=None):
#         env_id = super(nh_clinical_demo_env, self).create(cr, uid, vals, context)
#         data = self.read(cr, uid, env_id, [])
#         self.build(cr, uid, env_id)
#         _logger.debug("Env created id=%s data: %s" % (env_id, data))
#         return env_id
        
    def build(self, cr, uid, env_id, return_id=False):
        fake.seed(next_seed())
        env = self.browse(cr, uid, env_id)
        except_if(env.pos_id, msg="Build has already been executed for the env.id=%s" % env_id)
        self.build_pos(cr, uid, env_id)
        self.build_adt_users(cr, uid, env_id)
        self.build_nurse_users(cr, uid, env_id)
        self.build_ward_manager_users(cr, uid, env_id)
        self.build_ward_locations(cr, uid, env_id)
        self.build_bed_locations(cr, uid, env_id)
#         super(nh_clinical_demo_env, self).build(cr, uid, env_id)
        self.build_patients(cr, uid, env_id)
        if return_id:
            return env_id
        else:
            return self.browse(cr, uid, env_id)        
        if return_id:
            return env_id
        else:
            return self.browse(cr, uid, env_id)

    def build_bed_locations(self, cr, uid, env_id):
        env = self.browse(cr, SUPERUSER_ID, env_id)
        assert env.pos_id, "POS is not created/set in the env id=%s" % env_id
        fake.seed(next_seed())     
        location_pool = self.pool['nh.clinical.location']     
        location_ids = []
        for i in range(env.bed_qty): 
            d = self.fake_data(cr, uid, env_id, 'nh.clinical.location.bed') 
            location_ids.append(location_pool.create(cr, uid, d)) 
            _logger.debug("Bed location created id=%s data: %s" % (location_ids[-1], d))
        return location_pool.browse(cr, uid, location_ids)
    
    def build_ward_locations(self, cr, uid, env_id):
        fake.seed(next_seed())
        location_pool = self.pool['nh.clinical.location']
        env = self.browse(cr, SUPERUSER_ID, env_id)
        assert env.pos_id, "POS is not created/set in the env id=%s" % env_id   
        location_ids = []
        for i in range(env.ward_qty): 
            d = self.fake_data(cr, uid, env_id, 'nh.clinical.location.ward') 
            location_ids.append(location_pool.create(cr, uid, d)) 
            _logger.debug("Ward location created id=%s data: %s" % (location_ids[-1], d))
        return location_pool.browse(cr, uid, location_ids)
    
    def build_ward_manager_users(self, cr, uid, env_id):
        """
        By default responsible for all env's ward locations
        """
        fake.seed(next_seed())
        location_pool = self.pool['nh.clinical.location']
        imd_pool = self.pool['ir.model.data']
        user_pool = self.pool['res.users']
        env = self.browse(cr, SUPERUSER_ID, env_id)
        assert env.pos_id, "POS is not created/set in the env id=%s" % env_id
        group = imd_pool.get_object(cr, uid, "nh_clinical", "group_nhc_ward_manager")
        location_ids = location_pool.search(cr, uid, [['usage','=','ward'],['pos_id','=',env.pos_id.id]])
        user_ids = []
        for i in range(env.ward_manager_user_qty):
            name = fake.first_name()          
            data = {
                'name': "Ward Manager %s" % name,
                'login': self.data_unique_login(cr, uid, name.lower()),
                'password': name.lower(),
                'groups_id': [(4, group.id)],
                'location_ids': [(4,location_id) for location_id in location_ids]
            }  
            user_id = user_pool.create(cr, uid, data)  
            user_ids.append(user_id)
            _logger.debug("Ward Manager user created id=%s data: %s" % (user_id, data))
        return user_ids
 
    def build_nurse_users(self, cr, uid, env_id):
        """
        By default responsible for all env's ward locations
        """
        fake.seed(next_seed())
        location_pool = self.pool['nh.clinical.location']
        imd_pool = self.pool['ir.model.data']
        user_pool = self.pool['res.users']
        env = self.browse(cr, SUPERUSER_ID, env_id)
        assert env.pos_id, "POS is not created/set in the env id=%s" % env_id
        group = imd_pool.get_object(cr, uid, "nh_clinical", "group_nhc_nurse")
        location_ids = location_pool.search(cr, uid, [['usage','=','ward'],['pos_id','=',env.pos_id.id]])
        user_ids = []
        for i in range(env.nurse_user_qty):
            name = fake.first_name()          
            data = {
                'name': "Nurse %s" % name,
                'login': self.data_unique_login(cr, uid, name.lower()),
                'password': name.lower(),
                'groups_id': [(4, group.id)],
                'location_ids': [(4,location_id) for location_id in location_ids]
            }  
            user_id = user_pool.create(cr, uid, data)  
            user_ids.append(user_id)
            _logger.debug("Nurse user created id=%s data: %s" % (user_id, data))
        return user_ids

    def build_adt_users(self, cr, uid, env_id):
        fake.seed(next_seed())
        imd_pool = self.pool['ir.model.data']
        user_pool = self.pool['res.users']
        env = self.browse(cr, SUPERUSER_ID, env_id)
        assert env.pos_id, "POS is not created/set in the env id=%s" % env_id
        group = imd_pool.get_object(cr, uid, "nh_clinical", "group_nhc_adt")
        user_ids = []
        for i in range(env.adt_user_qty):
            data = {
                'name': env.pos_id.name,
                'login': self.data_unique_login(cr, uid, env.pos_id.location_id.code.lower()),
                'password': env.pos_id.location_id.code.lower(),
                'groups_id': [(4, group.id)],
                'pos_id': env.pos_id.id
            }  
            user_id = user_pool.create(cr, uid, data)  
            user_ids.append(user_id)
            _logger.debug("ADT user created id=%s data: %s" % (user_id, data))
        return user_ids
        
        # POS Location    
    def build_pos(self, cr, uid, env_id):
        fake.seed(next_seed())
        location_pool = self.pool['nh.clinical.location']
        pos_pool = self.pool['nh.clinical.pos']
        env = self.browse(cr, uid, env_id)
        # POS Location
        d = self.fake_data(cr, uid, env_id, 'nh.clinical.location.pos')
        pos_location_id = location_pool.create(cr, uid, d)
        _logger.debug("POS location created id=%s data: %s" % (pos_location_id, d))
        # POS Admission Lot
        d = self.fake_data(cr, uid, env_id, 'nh.clinical.location.admission', {'parent_id': pos_location_id})
        lot_admission_id = location_pool.create(cr, uid, d)
        _logger.debug("Admission location created id=%s data: %s" % (lot_admission_id, d))
        # POS Discharge Lot
        d = self.fake_data(cr, uid, env_id, 'nh.clinical.location.discharge', {'parent_id': pos_location_id})  
        lot_discharge_id = location_pool.create(cr, uid, d)       
        _logger.debug("Discharge location created id=%s data: %s" % (lot_discharge_id, d)) 
        # POS
        d = self.fake_data(cr, uid, env_id, 'nh.clinical.pos',
                            {
                            'location_id': pos_location_id,
                            'lot_admission_id': lot_admission_id,
                            'lot_discharge_id': lot_discharge_id,
                            })   
        pos_id = pos_pool.create(cr, uid, d)
        _logger.debug("POS created id=%s data: %s" % (pos_id, d))
        self.write(cr, uid, env_id, {'pos_id': pos_id})
        _logger.debug("Env updated pos_id=%s" % (pos_id))
        return pos_id 
    
#######################################################
########
########        Former activity types part
########
#######################################################
    def random_available_location(self, cr, uid, env_id, parent_id=None, usages=['bed'], available_range=[1,1]):
        fake.seed(next_seed())
        env = self.browse(cr, uid, env_id)
        location_ids = self.pool['nh.clinical.api'].location_map(cr, uid,  
                                                                  available_range=available_range,
                                                                  usages=['bed'],
                                                                  pos_ids=[env.pos_id.id]).keys()
        location_pool = self.pool['nh.clinical.location']
#         if parent_id:
#             domain = [['id', 'child_of', parent_id]]
#             location_ids = location_pool.search(cr, uid, domain)
        if not location_ids:
            _logger.warn("No available locations left!")
        location_id = location_ids and fake.random_element(location_ids) or False
        return location_pool.browse(cr, uid, location_id)

    def get_activity_free_patients(self, cr, uid, env_id, data_models, states):
        # random_observation_available_location
        fake.seed(next_seed())
        env = self.browse(cr, uid, env_id)
        patient_pool = self.pool['nh.clinical.patient']
        api_pool = self.pool['nh.clinical.api']
        all_patient_ids = [a.patient_id.id for a in api_pool.get_activities(cr, SUPERUSER_ID, pos_ids=[env.pos_id.id], data_models=['nh.clinical.spell'], states=['started'])]
        used_patient_ids = [a.patient_id.id for a in api_pool.get_activities(cr, SUPERUSER_ID, data_models=data_models, states=states)]
        patient_ids = list(set(all_patient_ids)-set(used_patient_ids))       
        #patient_id = patient_ids and fake.random_element(patient_ids) or False
        return patient_pool.browse(cr, SUPERUSER_ID, patient_ids)

    def data_adt_patient_discharge(self, cr, uid, env_id, activity_id=None, data={}):
        fake.seed(next_seed())
        env = self.browse(cr, uid, env_id)
        patient_ids = self.get_patient_ids(cr, uid, env_id, 'nh.clinical.spell', [['activity_id.date_terminated','=',False]])
        patient = self.pool['nh.clinical.patient'].browse(cr, uid, fake.random_element(patient_ids))
        d = {
            'other_identifier': patient.other_identifier,
            'pos_id': env.pos_id.id
        }
        d.update(data)
        return d

    def data_adt_patient_cancel_admit(self, cr, uid, env_id, activity_id=None, data={}):
        fake.seed(next_seed())
        env = self.browse(cr, uid, env_id)
        patient_ids = self.get_patient_ids(cr, uid, env_id, 'nh.clinical.spell', [['activity_id.date_terminated','=',False]])
        patient = self.pool['nh.clinical.patient'].browse(cr, uid, fake.random_element(patient_ids))
        d = {
            'other_identifier': patient.other_identifier,
            'pos_id': env.pos_id.id
        }
        d.update(data)
        return d

    def data_adt_patient_admit(self, cr, uid, env_id, activity_id=None, data={}):
        """
        """
        fake.seed(next_seed())
        env = self.browse(cr, SUPERUSER_ID, env_id)
        patient_pool = self.pool['nh.clinical.patient']
        location_pool = self.pool['nh.clinical.location']
        
        reg_patient_ids = self.get_patient_ids(cr, uid, env_id)
        admit_patient_ids = self.get_patient_ids(cr, uid, env_id, 'nh.clinical.adt.patient.admit')
        patient_ids = list(set(reg_patient_ids) - set(admit_patient_ids))
        assert patient_ids, "No patients left to admit!"
        patients = patient_pool.browse(cr, uid, patient_ids)
        locations = self.pool['nh.clinical.api'].get_locations(cr, uid, pos_ids=[env.pos_id.id], usages=['ward'], available_range=[0,999])
        assert locations, "No ward locations to set as admit location"
        d = {
            'other_identifier': fake.random_element(patients).other_identifier,
            'location': fake.random_element(locations).code,
            'code': fake.random_int(min=10001, max=99999),
            'start_date': fake.date_time_between(start_date="-1w", end_date="-1h").strftime("%Y-%m-%d %H:%M:%S"),
            'doctors': [
                   {
                    'code': str(fake.random_int(min=10001, max=99999)),
                    'type': fake.random_element(('r','c')),
                    'title': fake.random_element(('Mr','Mrs','Ms','Dr')),
                    'family_name': fake.last_name(),
                    'given_name': fake.first_name()
                    },
                   ]
             }
        d.update(data)
        return d


    def data_adt_patient_register(self, cr, uid, env_id, activity_id=None, data={}):
        fake.seed(next_seed())
        gender = fake.random_element(('M','F'))
        d = {
                'family_name': fake.last_name(),
                'given_name': fake.first_name(),
                'other_identifier': str(fake.random_int(min=1000001, max=9999999)),
                'dob': fake.date_time_between(start_date="-80y", end_date="-10y").strftime("%Y-%m-%d %H:%M:%S"),
                'gender': gender,
                'sex': gender,
                }
        d.update(data)
        return d
        
        

    def data_observation_ews(self, cr, uid, env_id, activity_id=None, data={}):
        fake.seed(next_seed())
        patients = self.get_activity_free_patients(cr, uid, env_id,['nh.clinical.patient.observation.ews'],['new','scheduled','started'])
        d = {
            'respiration_rate': fake.random_int(min=5, max=34),
            'indirect_oxymetry_spo2': fake.random_int(min=85, max=100),
            'body_temperature': float(fake.random_int(min=350, max=391))/10.0 ,
            'blood_pressure_systolic': fake.random_int(min=65, max=206),
            'pulse_rate': fake.random_int(min=35, max=136),
            'avpu_text': fake.random_element(('A', 'V', 'P', 'U')),
            'oxygen_administration_flag': fake.random_element((True, False)),
            'blood_pressure_diastolic': fake.random_int(min=35, max=176),
            'patient_id': patients and fake.random_element(patients).id or False
        }
        if d['oxygen_administration_flag']:
            d.update({
                'flow_rate': fake.random_int(min=40, max=60),
                'concentration': fake.random_int(min=50, max=100),
                'cpap_peep': fake.random_int(min=1, max=100),
                'niv_backup': fake.random_int(min=1, max=100),
                'niv_ipap': fake.random_int(min=1, max=100),
                'niv_epap': fake.random_int(min=1, max=100),
            })
        if not d['patient_id']:
            _logger.warn("No patients available for ews!")
        d.update(data)
        return d    
    
        
    def data_observation_stools(self, cr, uid, env_id, activity_id=None, data={}):
        fake.seed(next_seed()) 
        d = {
            'bowel_open': fake.random_int(min=0, max=1),
            'nausea': fake.random_int(min=0, max=1),
            'vomiting': fake.random_int(min=0, max=1),
            'quantity': fake.random_element(('large', 'medium', 'small')),
            'colour': fake.random_element(('brown', 'yellow', 'green', 'black', 'red', 'clay')),
            'bristol_type': str(fake.random_int(min=1, max=7)),
            'offensive': fake.random_int(min=0, max=1),
            'strain': fake.random_int(min=0, max=1),
            'laxatives': fake.random_int(min=0, max=1),
            'samples': fake.random_element(('none', 'micro', 'virol', 'm+v')),
            'rectal_exam': fake.random_int(min=0, max=1),
            'patient_id': fake.random_element(self.get_current_patient_ids(cr, SUPERUSER_ID, env_id))
        }
        d.update(data)
        return d

    def data_observation_blood_sugar(self, cr, uid, env_id, activity_id=None, data={}):
        fake.seed(next_seed())
        d = data.copy()
        d = {
             'blood_sugar': float(fake.random_int(min=1, max=100)),
             'patient_id': fake.random_element(self.get_current_patient_ids(cr, SUPERUSER_ID, env_id))
        }
        d.update(data)
        return d


    def data_observation_blood_product(self, cr, uid, env_id, activity_id=None, data={}):
        fake.seed(next_seed())
        d = {
             'product': fake.random_element(('rbc', 'ffp', 'platelets', 'has', 'dli', 'stem')),
             'vol': float(fake.random_int(min=1, max=10)),
             'patient_id': fake.random_element(self.get_current_patient_ids(cr, SUPERUSER_ID, env_id))
        }
        d.update(data)
        return d

    
    def data_observation_weight(self, cr, uid, env_id, activity_id=None, data={}):
        fake.seed(next_seed())
        d = {
             'weight': float(fake.random_int(min=40, max=200)),
             'patient_id': fake.random_element(self.get_current_patient_ids(cr, SUPERUSER_ID, env_id))
        }
        d.update(data)
        return d


    def data_observation_height(self, cr, uid, env_id, activity_id=None, data={}):
        fake.seed(next_seed())
        d = {
             'height': float(fake.random_int(min=160, max=200))/100.0,
             'patient_id': fake.random_element(self.get_current_patient_ids(cr, SUPERUSER_ID, env_id))
        }
        d.update(data)
        return d

    
    def data_placement(self, cr, uid, env_id, activity_id=None, data={}):
        fake.seed(next_seed())
        d = {
             'location_id': self.random_available_location(cr, uid, env_id).id
        }
        if not d['location_id']:
            _logger.warn("No available locations left!")
        d.update(data)
        return d

                
    def data_observation_gcs(self, cr, uid, env_id, activity_id=None, data={}):    
        fake.seed(next_seed())
        patients = self.get_activity_free_patients(cr, uid, env_id,['nh.clinical.patient.observation.gcs'],['new','scheduled','started']) 
        d = {
            'eyes': fake.random_element(('1', '2', '3', '4', 'C')),
            'verbal': fake.random_element(('1', '2', '3', '4', '5', 'T')),
            'motor': fake.random_element(('1', '2', '3', '4', '5', '6')),
            'patient_id': patients and fake.random_element(patients).id or False
        }
        if not d['patient_id']:
            _logger.warn("No patients available for gcs!")        
        d.update(data)
        return d                

    def get_patient_ids(self, cr, uid, env_id, data_model='nh.clinical.adt.patient.register', domain=[]):
        domain_copy = domain[:]     
        env = self.browse(cr, SUPERUSER_ID, env_id)
        assert env.pos_id, "POS is not created/set in the env id=%s" % env_id
        model_pool = self.pool[data_model]
        domain_copy.append(['activity_id.pos_id','=',env.pos_id.id])
        model_ids = model_pool.search(cr, uid, domain_copy)
        patient_ids = [m.patient_id.id for m in model_pool.browse(cr, uid, model_ids)]       
        return patient_ids
    
    def get_current_patient_ids(self, cr, uid, env_id):
        patient_ids = self.get_patient_ids(cr, uid, env_id, 'nh.clinical.spell', [['activity_id.date_terminated','=',False]])
        return patient_ids   
        
    def get_adt_user_ids(self, cr, uid, env_id):
        user_pool = self.pool['res.users']
        imd_pool = self.pool['ir.model.data']
        env = self.browse(cr, SUPERUSER_ID, env_id)
        assert env.pos_id, "POS is not created/set in the env id=%s" % env_id
        adt_group = imd_pool.get_object(cr, uid, "nh_clinical", "group_nhc_adt")
        ids = user_pool.search(cr, uid, [['groups_id','in',adt_group.id],['pos_id','=',env.pos_id.id]])
        return ids

    def create(self, cr, uid, vals={},context=None):
        env_id = super(nh_clinical_demo_env, self).create(cr, uid, vals, context)
        #env_id = isinstance(env_id, (int, long)) and env_id or env_id.id
        data = self.read(cr, uid, env_id, [])
        _logger.debug("Env created id=%s data: %s" % (env_id, data))
        return env_id

    def build_patients(self, cr, uid, env_id):
        fake.seed(next_seed())
        env = self.browse(cr, SUPERUSER_ID, env_id)
        assert env.pos_id, "POS is not created/set in the env id=%s" % env_id
        api = self.pool['nh.clinical.api']
        adt_user_id = self.get_adt_user_ids(cr, uid, env_id)[0]
        for i in range(env.patient_qty):
            register_activity = self.create_complete(cr, adt_user_id, env_id, 'nh.clinical.adt.patient.register', {}, {})
            admit_data = {'other_identifier': register_activity.data_ref.other_identifier}
            admit_activity = self.create_complete(cr, adt_user_id, env_id, 'nh.clinical.adt.patient.admit', {}, admit_data)
            placement_activity = api.get_activities(cr, uid, 
                                                         pos_ids = [env.pos_id.id],
                                                         data_models=['nh.clinical.patient.placement'],
                                                         states=['new'])[0]
            self.submit_complete(cr, adt_user_id, env_id, placement_activity.id) 
        return True    