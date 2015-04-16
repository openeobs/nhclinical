# -*- coding: utf-8 -*-

from datetime import datetime as dt
import logging

from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from openerp import SUPERUSER_ID

from openerp.addons.nh_activity.activity import except_if

_logger = logging.getLogger(__name__)


class nh_clinical_adt(orm.Model):
    _name = 'nh.clinical.adt'
    _inherit = ['nh.activity.data']     
    _columns = {
    }


class nh_clinical_adt_patient_register(orm.Model):
    """
    Registers a new patient into the system.
     patient_identifier: String - NHS Number
     other_identifier: String - Hospital Number
     given_name: String - First name
     family_name: String - Last name
     middle_names: String - Middle names
     dob: String - Date of Birth, have to be in format '%Y-%m-%d %H:%M:%S'
     gender: String - 'BOTH','F','I','M','NSP','U'
     sex: String - Same values as gender.
     ethnicity: String - Look at patient class for the list of allowed values.
    """
    _name = 'nh.clinical.adt.patient.register'
    _inherit = ['nh.activity.data']   
    _description = 'ADT Patient Register'   
    _columns = { 
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient'),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS', required=True),
        'patient_identifier': fields.text('patientId'),
        'other_identifier': fields.text('otherId'),
        'family_name': fields.text('familyName'),
        'given_name': fields.text('givenName'),
        'middle_names': fields.text('middleName'),  
        'dob': fields.datetime('DOB'),
        'gender': fields.char('Gender'),
        'sex': fields.char('Sex'),
        'ethnicity': fields.char('Ethnicity'),
        'title': fields.many2one('res.partner.title', 'Title')
    }
    
    def submit(self, cr, uid, activity_id, vals, context=None):
        vals_copy = vals.copy()
        res = {}
        user = self.pool['res.users'].browse(cr, uid, uid, context)
        except_if(not user.pos_id or not user.pos_id.location_id, msg="POS location is not set for user.login = %s!" % user.login)        
        except_if(not 'patient_identifier' in vals_copy.keys() and not 'other_identifier' in vals_copy.keys(),
              msg="patient_identifier or other_identifier not found in submitted data!")
        patient_pool = self.pool['nh.clinical.patient']
        patient_domain = [(k, '=', v) for k, v in vals_copy.iteritems() if k == 'other_identifier']
        if not patient_domain:
            patient_domain = [(k, '=', v) for k, v in vals_copy.iteritems() if k == 'patient_identifier']
        patient_id = patient_pool.search(cr, uid, patient_domain)
        except_if(patient_id, msg="Patient already exists! Data: %s" % vals_copy)
        if vals_copy.get('title'):
            title_pool = self.pool['res.partner.title']
            titles = title_pool.read(cr, uid, title_pool.search(cr, uid, [], context=context), ['id', 'name'], context=context)
            title_id = False
            for t in titles:
                if t['name'].replace('.', '').lower() == vals_copy.get('title').replace('.', '').lower():
                    title_id = t['id']
                    break
            if not title_id:
                title_id = title_pool.create(cr, uid, {'name': vals_copy.get('title')})
            vals_copy.update({'title': title_id})
        # patient_id = patient_pool.create(cr, uid, vals_copy, context)
        vals_copy.update({'pos_id': user.pos_id.id})
        super(nh_clinical_adt_patient_register, self).submit(cr, uid, activity_id, vals_copy, context)
        # res.update({'patient_id': patient_id})
        return res
    
    def complete(self, cr, uid, activity_id, context=None): 
        res = {}
        activity_pool = self.pool['nh.activity']
        register_activity = activity_pool.browse(cr, uid, activity_id, context=context)
        patient_pool = self.pool['nh.clinical.patient']
        vals = {
            'title': register_activity.data_ref.title.id,
            'patient_identifier': register_activity.data_ref.patient_identifier,
            'other_identifier': register_activity.data_ref.other_identifier,
            'family_name': register_activity.data_ref.family_name,
            'given_name': register_activity.data_ref.given_name,
            'middle_names': register_activity.data_ref.middle_names,
            'dob': register_activity.data_ref.dob,
            'gender': register_activity.data_ref.gender,
            'sex': register_activity.data_ref.sex,
            'ethnicity': register_activity.data_ref.ethnicity
        }
        patient_id = patient_pool.create(cr, uid, vals, context)
        self.write(cr, uid, register_activity.data_ref.id, {'patient_id': patient_id}, context=context)
        super(nh_clinical_adt_patient_register, self).complete(cr, uid, activity_id, context)
        return res


class nh_clinical_adt_patient_admit(orm.Model):
    """
        adt.patient.admit: 
            - validate patient(patient_id), suggested_location(location_id or false)
            - on validation fail raise exception
            - start admission with patient_id and suggested_location
            
       consulting and referring doctors are expected in the submitted values on key='doctors' in format:
       [...
       {
       'type': 'c' or 'r',
       'code': code string,
       'title':, 'given_name':, 'family_name':, }
       ...]
       
       if doctor doesn't exist, we create partner, but don't create user
        
             
    """
    
    _name = 'nh.clinical.adt.patient.admit'
    _inherit = ['nh.activity.data']      
    _description = 'ADT Patient Admit'    
    _columns = {
        'suggested_location_id': fields.many2one('nh.clinical.location', 'Suggested Location', help="Location suggested by ADT for placement. Usually ward."),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS', required=True),
        'location': fields.text('Location'),
        'code': fields.text("Code"),
        'start_date': fields.datetime("ADT Start Date"), 
        'other_identifier': fields.text("Other Identifier"),
        'doctors': fields.text("Doctors"),
        'ref_doctor_ids': fields.many2many('nh.clinical.doctor', 'ref_doctor_admit_rel', 'admit_id', 'doctor_id', "Referring Doctors"),
        'con_doctor_ids': fields.many2many('nh.clinical.doctor', 'con_doctor_admit_rel', 'admit_id', 'doctor_id', "Consulting Doctors"),
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        res = {}
        api_pool = self.pool['nh.clinical.api']
        user = self.pool['res.users'].browse(cr, uid, uid, context)

        if not user.pos_id or not user.pos_id.location_id:
            raise orm.except_orm('Exception!', msg="POS location is not set for user.login = %s!" % user.login)

        # location validation
        suggested_location = api_pool.get_locations(cr, SUPERUSER_ID, codes=[vals['location']], pos_ids=[user.pos_id.id])
        if not suggested_location:
            _logger.warn("ADT suggested_location '%s' not found! Will automatically create one" % vals['location'])
            location_pool = self.pool['nh.clinical.location']
            suggested_location_id = location_pool.create(cr, uid, {
                'name': vals['location'],
                'code': vals['location'],
                'pos_id': user.pos_id.id,
                'type': 'poc',
                'usage': 'ward'
            }, context=context)
        else:
            suggested_location_id = suggested_location[0].id
        # patient validation
        patient_pool = self.pool['nh.clinical.patient']
        patient_id = patient_pool.search(cr, SUPERUSER_ID, [('other_identifier', '=', vals['other_identifier'])])
        except_if(not patient_id, msg="Patient not found!")

        if len(patient_id) > 1:
            _logger.warn("More than one patient found with 'other_identifier' = %s! Passed patient_id = %s" 
                                    % (vals['other_identifier'], patient_id[0]))
        patient_id = patient_id[0]
        vals_copy = vals.copy()       
        vals_copy.update({'suggested_location_id': suggested_location_id, 'patient_id': patient_id, 'pos_id': user.pos_id.id})  
        # doctors
        if vals.get('doctors'):
            try:
                doctors = eval(str(vals['doctors']))
                ref_doctor_ids = []
                con_doctor_ids = []
                doctor_pool = self.pool['nh.clinical.doctor']
                for d in doctors:
                    doctor_id = doctor_pool.search(cr, uid, [['code', '=', d.get('code')]], context=context)
                    if not doctor_id:
                        title_id = False
                        if d.get('title'):
                            d['title'] = d['title'].strip()
                            title_pool = self.pool['res.partner.title']
                            title_id = title_pool.search(cr, uid, [['name', '=', d['title']]], context=context)
                            title_id = title_id[0] if title_id else title_pool.create(cr, uid, {'name': d['title']}, context=context)
                        data = {
                                'name': "%s, %s" % (d['family_name'], d['given_name']),
                                'title': title_id,
                                'code': d.get('code'),
                                'gender': d.get('gender'),
                                'gmc': d.get('gmc')
                                }
                        doctor_id = doctor_pool.create(cr, uid, data, context=context)
                    else:
                        if doctor_id > 1:
                            _logger.warn("More than one doctor found with code '%s' passed id=%s" % (d.get('code'), doctor_id[0]))
                        doctor_id = doctor_id[0]
                    ref_doctor_ids.append(doctor_id) if d['type'] == 'r' else con_doctor_ids.append(doctor_id)
                ref_doctor_ids and vals_copy.update({'ref_doctor_ids': [[6, False, ref_doctor_ids]]})
                con_doctor_ids and vals_copy.update({'con_doctor_ids': [[6, False, con_doctor_ids]]})
            except:
                _logger.warn("Can't evaluate 'doctors': %s" % (vals['doctors']))
        super(nh_clinical_adt_patient_admit, self).submit(cr, uid, activity_id, vals_copy, context)
        return res 

    def complete(self, cr, uid, activity_id, context=None):
        res = {}
        super(nh_clinical_adt_patient_admit, self).complete(cr, uid, activity_id, context)
        api_pool = self.pool['nh.clinical.api']
        admit_activity = api_pool.get_activity(cr, uid, activity_id)
        admission_activity = api_pool.create_complete(cr, SUPERUSER_ID, 'nh.clinical.patient.admission',
                                       {'creator_id': activity_id}, 
                                       # FIXME! pos_id should be taken from adt_user.pos_id
                                       {'pos_id': admit_activity.data_ref.suggested_location_id.pos_id.id,
                                        'patient_id': admit_activity.patient_id.id,
                                        'suggested_location_id': admit_activity.data_ref.suggested_location_id.id,
                                        'code': admit_activity.data_ref.code,
                                        'start_date': admit_activity.data_ref.start_date})
        spell_activity = [a for a in admission_activity.created_ids if a.data_model == 'nh.clinical.spell'][0]
        api_pool.write_activity(cr, SUPERUSER_ID, activity_id, {'parent_id': spell_activity.id})
        return res  

    
class nh_clinical_adt_patient_cancel_admit(orm.Model):
    """
    Cancels the last admission of the patient. Cancels the current patient spell.
    """
    _name = 'nh.clinical.adt.patient.cancel_admit'
    _inherit = ['nh.activity.data']  
    _description = 'ADT Cancel Patient Admit'    
    _columns = {
        'other_identifier': fields.text('otherId', required=True),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS', required=True),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        user = self.pool['res.users'].browse(cr, uid, uid, context)
        except_if(not user.pos_id or not user.pos_id.location_id, msg="POS location is not set for user.login = %s!" % user.login)
        patient_pool = self.pool['nh.clinical.patient']
        patient_id = patient_pool.search(cr, SUPERUSER_ID, [('other_identifier','=',vals['other_identifier'])])
        except_if(not patient_id, msg="Patient not found!")
        if len(patient_id) > 1:
            _logger.warn("More than one patient found with 'other_identifier' = %s! Passed patient_id = %s" 
                                    % (vals['other_identifier'], patient_id[0]))
        patient_id = patient_id[0]        
        vals_copy = vals.copy()
        vals_copy.update({'pos_id': user.pos_id.id, 'patient_id':patient_id})
        res = super(nh_clinical_adt_patient_cancel_admit, self).submit(cr, uid, activity_id, vals_copy, context)
        return res

    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        admit_cancel_activity = activity_pool.browse(cr, uid, activity_id)
        # get admit activity
        api_pool = self.pool['nh.clinical.api']
        spell_activity = api_pool.get_patient_spell_activity_browse(cr, SUPERUSER_ID, admit_cancel_activity.data_ref.patient_id.id, context=context)
        except_if(not spell_activity, msg="Patient id=%s has no started spell!" % admit_cancel_activity.data_ref.patient_id.id)
        # admit-admission-spell
        admit_activity_id = spell_activity.creator_id \
                            and spell_activity.creator_id.creator_id\
                            and spell_activity.creator_id.creator_id.id \
                            or False
        except_if(not admit_activity_id, msg="adt.admit activity is not found!")
        admit_activity = activity_pool.browse(cr, uid, admit_activity_id)
        # get all children and created activity_ids
        activity_ids = []
        next_level_activity_ids = []

        next_level_activity_ids.extend([child.id for child in admit_activity.child_ids])
        next_level_activity_ids.extend([created.id for created in admit_activity.created_ids])
        activity_ids.extend(next_level_activity_ids)
        while next_level_activity_ids:
            for activity in activity_pool.browse(cr, uid, next_level_activity_ids):
                next_level_activity_ids = [child.id for child in activity.child_ids]
                next_level_activity_ids.extend([created.id for created in activity.created_ids])            
                activity_ids.extend(next_level_activity_ids)
        activity_ids = list(set(activity_ids)) 
        activity_id in activity_ids and activity_ids.remove(activity_id)
        _logger.info("Starting activities cancellation due to adt.pateint.cancel_admit activity completion...")       
        for activity in activity_pool.browse(cr, uid, activity_ids):
            if activity.state not in ['completed', 'cancelled']:
                activity_pool.cancel(cr, uid, activity.id)
        res = super(nh_clinical_adt_patient_cancel_admit, self).complete(cr, uid, activity_id, context)
        return res


class nh_clinical_adt_patient_discharge(orm.Model):
    """
    Discharge a patient from the hospital. Completes the patient spell.
    """
    _name = 'nh.clinical.adt.patient.discharge'
    _inherit = ['nh.activity.data']  
    _description = 'ADT Patient Discharge'
    _columns = {
        'other_identifier': fields.text('otherId', required=True),
        'discharge_date': fields.datetime('Discharge Date'),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS', required=True),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True)
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        res = {}
        user = self.pool['res.users'].browse(cr, uid, uid, context)
        except_if(not user.pos_id or not user.pos_id.location_id, msg="POS location is not set for user.login = %s!" % user.login)
        # patient validation
        patient_pool = self.pool['nh.clinical.patient']
        patient_id = patient_pool.search(cr, SUPERUSER_ID, [('other_identifier', '=', vals['other_identifier'])])
        except_if(not patient_id, msg="Patient not found!")
        if len(patient_id) > 1:
            _logger.warn("More than one patient found with 'other_identifier' = %s! Passed patient_id = %s"
                                    % (vals['other_identifier'], patient_id[0]))
        patient_id = patient_id[0]
        # discharge date
        discharge_date = vals.get('discharge_date') if vals.get('discharge_date') else dt.now().strftime(DTF)
        vals_copy = vals.copy()
        vals_copy.update({'patient_id': patient_id, 'pos_id': user.pos_id.id, 'discharge_date': discharge_date})
        super(nh_clinical_adt_patient_discharge, self).submit(cr, uid, activity_id, vals_copy, context)
        return res

    def complete(self, cr, uid, activity_id, context=None):
        res = {}
        activity_pool = self.pool['nh.activity']
        api_pool = self.pool['nh.clinical.api']
        patient_pool = self.pool['nh.clinical.patient']
        discharge_activity = activity_pool.browse(cr, SUPERUSER_ID, activity_id, context=context)
        patient_id = patient_pool.search(cr, SUPERUSER_ID, [('other_identifier', '=', discharge_activity.data_ref.other_identifier)], context=context)
        except_if(not patient_id, msg="Patient not found!")
        patient_id = patient_id[0]
        spell_activity = api_pool.get_patient_spell_activity_browse(cr, SUPERUSER_ID, patient_id, context=context)
        except_if(not spell_activity.id, msg="Patient was not admitted!")
        res = super(nh_clinical_adt_patient_discharge, self).complete(cr, uid, activity_id, context)
        discharge_pool = self.pool['nh.clinical.patient.discharge']
        discharge_activity_id = discharge_pool.create_activity(
            cr, SUPERUSER_ID,
            {'creator_id': activity_id,
             'parent_id': spell_activity.id},
            {'patient_id': patient_id,
             'discharge_date': discharge_activity.data_ref.discharge_date}, context=context)
        activity_pool.complete(cr, SUPERUSER_ID, discharge_activity_id, context=context)
        return res 


class nh_clinical_adt_patient_transfer(orm.Model):
    """
    Transfers a patient from a location to another location.
    It will trigger admission policy in the destination location.
    """
    _name = 'nh.clinical.adt.patient.transfer'
    _inherit = ['nh.activity.data']
    _description = 'ADT Patient Transfer'      
    _columns = {
        'patient_identifier': fields.text('patientId'),
        'other_identifier': fields.text('otherId'),                
        'location': fields.text('Location'),
        'from_location_id': fields.many2one('nh.clinical.location', 'Origin Location'),
        'location_id': fields.many2one('nh.clinical.location', 'Transfer Location'),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS', required=True),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True)
    }
    
    def submit(self, cr, uid, activity_id, vals, context=None):
        user = self.pool['res.users'].browse(cr, uid, uid, context)
        except_if(not user.pos_id or not user.pos_id.location_id, msg="POS location is not set for user.login = %s!" % user.login)
        except_if(not ('other_identifier' in vals or 'patient_identifier' in vals), msg="patient_identifier or other_identifier not found in submitted data!")
        patient_pool = self.pool['nh.clinical.patient']
        location_pool = self.pool['nh.clinical.location']
        activity_pool = self.pool['nh.activity']
        api_pool = self.pool['nh.clinical.api']
        other_identifier = vals.get('other_identifier')
        patient_identifier = vals.get('patient_identifier')
        domain = []
        other_identifier and domain.append(('other_identifier', '=', other_identifier))
        patient_identifier and domain.append(('patient_identifier', '=', patient_identifier))
        domain = domain and ['|']*(len(domain)-1) + domain
        patient_id = patient_pool.search(cr, uid, domain)
        except_if(not patient_id, msg="Patient not found!")

        spell_activity_id = api_pool.get_patient_spell_activity_id(cr, uid, patient_id[0], context=context)
        except_if(not spell_activity_id, msg="Active spell not found for patient.id=%s !" % patient_id[0])
        spell_activity = activity_pool.browse(cr, uid, spell_activity_id, context=context)
        patient_id = patient_id[0]           
        location_pool = self.pool['nh.clinical.location']
        location_id = location_pool.search(cr, uid, [('code', '=', vals['location'])], context=context)
        if not location_id:
            _logger.warn("ADT transfer location '%s' not found! Will automatically create one" % vals['location'])
            location_pool = self.pool['nh.clinical.location']
            location_id = location_pool.create(cr, uid, {
                'name': vals['location'],
                'code': vals['location'],
                'pos_id': spell_activity.location_id.pos_id.id,
                'type': 'poc',
                'usage': 'ward'
            }, context=context)
        else:
            location_id = location_id[0]

        domain = [('data_model', '=', 'nh.clinical.patient.move'),
                  ('state', '=', 'completed'),
                  ('patient_id', '=', patient_id)]
        move_activity_ids = activity_pool.search(cr, uid, domain, order='date_terminated desc, sequence desc', context=context)
        move_activity = activity_pool.browse(cr, uid, move_activity_ids[0], context=context)
        vals_copy = vals.copy()
        if move_activity.location_id.type == 'poc':
            if move_activity.location_id.usage == 'ward':
                last_location_id = move_activity.location_id.id
            else:
                last_location_id = location_pool.get_closest_parent_id(cr, uid, move_activity.location_id.id, 'ward', context=context)
        else:
            domain = [('state', '=', 'completed'),
                      ('patient_id', '=', patient_id),
                      ('data_model', 'in', ['nh.clinical.adt.patient.admit', 'nh.clinical.adt.spell.update',
                                            'nh.clinical.adt.patient.transfer', 'nh.clinical.adt.patient.cancel_transfer'])]
            op_activity_ids = activity_pool.search(cr, uid, domain, order='date_terminated desc, sequence desc', context=context)
            latest_op = activity_pool.browse(cr, uid, op_activity_ids[0], context=context)
            if latest_op.data_model in ['nh.clinical.adt.patient.admit', 'nh.clinical.adt.spell.update']:
                last_location_id = latest_op.data_ref.suggested_location_id.id
            elif latest_op.data_model == 'nh.clinical.adt.patient.cancel_transfer':
                last_location_id = latest_op.data_ref.last_location_id.id
            else:
                last_location_id = latest_op.data_ref.location_id.id

        vals_copy.update({'patient_id': patient_id, 'pos_id': user.pos_id.id, 'location_id': location_id, 'from_location_id': last_location_id})
        super(nh_clinical_adt_patient_transfer, self).submit(cr, uid, activity_id, vals_copy, context)

    def complete(self, cr, uid, activity_id, context=None):
        res = {}
        super(nh_clinical_adt_patient_transfer, self).complete(cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        api_pool = self.pool['nh.clinical.api']
        move_pool = self.pool['nh.clinical.patient.move']
        transfer_activity = activity_pool.browse(cr, SUPERUSER_ID, activity_id, context=context)
        # patient move
        spell_activity_id = api_pool.get_patient_spell_activity_id(cr, SUPERUSER_ID, transfer_activity.patient_id.id, context=context)
        except_if(not spell_activity_id, msg="Spell not found!")
        move_activity_id = move_pool.create_activity(cr, SUPERUSER_ID, {
            'parent_id': spell_activity_id,
            'creator_id': activity_id
        }, {
            'patient_id': transfer_activity.patient_id.id,
            'location_id': transfer_activity.data_ref.location_id.id},
            context=context)
        res[move_pool._name] = move_activity_id
        activity_pool.complete(cr, SUPERUSER_ID, move_activity_id, context)
        # trigger policy activities
        self.trigger_policy(cr, uid, activity_id, location_id=transfer_activity.data_ref.location_id.id, context=context)
        return res
        

class nh_clinical_adt_patient_merge(orm.Model):
    """
    Merges a patient into another patient making the resulting patient own all activities.
    """
    _name = 'nh.clinical.adt.patient.merge'
    _inherit = ['nh.activity.data'] 
    _description = 'ADT Patient Merge'
    _columns = {
        'from_identifier': fields.text('From patient Identifier'),
        'into_identifier': fields.text('Into Patient Identifier'),        
    }

    def complete(self, cr, uid, activity_id, context=None):
        res = {}
        super(nh_clinical_adt_patient_merge, self).complete(cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        merge_activity = activity_pool.browse(cr, SUPERUSER_ID, activity_id, context=context)
        except_if(not (merge_activity.data_ref.from_identifier and merge_activity.data_ref.into_identifier), msg="from_identifier or into_identifier not found in submitted data!")
        patient_pool = self.pool['nh.clinical.patient']
        from_id = patient_pool.search(cr, uid, [('other_identifier', '=', merge_activity.data_ref.from_identifier)])
        into_id = patient_pool.search(cr, uid, [('other_identifier', '=', merge_activity.data_ref.into_identifier)])
        except_if(not(from_id and into_id), msg="Source or destination patient not found!")
        from_id = from_id[0]
        into_id = into_id[0]
        # compare and combine data. may need new cursor to have the update in one transaction
        for model_name in self.pool.models.keys():
            model_pool = self.pool[model_name]
            if model_name.startswith("nh.clinical") and model_pool._auto and 'patient_id' in model_pool._columns.keys() and model_name != self._name and model_name != 'nh.clinical.notification' and model_name != 'nh.clinical.patient.observation':
                ids = model_pool.search(cr, uid, [('patient_id', '=', from_id)], context=context)
                if ids:
                    model_pool.write(cr, uid, ids, {'patient_id': into_id}, context=context)
        activity_ids = activity_pool.search(cr, uid, [('patient_id', '=', from_id)], context=context)
        activity_pool.write(cr, uid, activity_ids, {'patient_id': into_id}, context=context)
        from_data = patient_pool.read(cr, uid, from_id, context)
        into_data = patient_pool.read(cr, uid, into_id, context)
        vals_into = {}
        for fk, fv in from_data.iteritems():
            if not fv:
                continue
            if fv and into_data[fk] and fv != into_data[fk]:
                pass
            if fv and not into_data[fk]:
                if '_id' == fk[-3:]:
                    vals_into.update({fk: fv[0]})
                else:
                    vals_into.update({fk: fv})
        res['merge_into_update'] = patient_pool.write(cr, uid, into_id, vals_into, context)
        res['merge_from_deactivate'] = patient_pool.write(cr, uid, from_id, {'active': False}, context)
        return res
        

class nh_clinical_adt_patient_update(orm.Model):
    """
    Update patient information.
    """
    _name = 'nh.clinical.adt.patient.update'
    _inherit = ['nh.activity.data'] 
    _description = 'ADT Patient Update'     
    _columns = {
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
        'patient_identifier': fields.text('patientId'),
        'other_identifier': fields.text('otherId'),
        'family_name': fields.text('familyName'),
        'given_name': fields.text('givenName'),
        'middle_names': fields.text('middleName'),
        'dob': fields.datetime('DOB'),
        'gender': fields.char('Gender', size=1),
        'sex': fields.char('Sex', size=1),
        'title': fields.many2one('res.partner.title', 'Title')
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        vals_copy = vals.copy()
        user = self.pool['res.users'].browse(cr, uid, uid, context)
        except_if(not user.pos_id or not user.pos_id.location_id, msg="POS location is not set for user.login = %s!" % user.login)
        except_if(not 'patient_identifier' in vals_copy.keys() and not 'other_identifier' in vals_copy.keys(),
              msg="patient_identifier or other_identifier not found in submitted data!")
        patient_pool = self.pool['nh.clinical.patient']
        hospital_number = vals_copy.get('other_identifier')
        nhs_number = vals_copy.get('patient_identifier')
        if hospital_number:
            patient_domain = [('other_identifier', '=', hospital_number)]
            del vals_copy['other_identifier']
        else:
            patient_domain = [('patient_identifier', '=', nhs_number)]
            del vals_copy['patient_identifier']
        patient_id = patient_pool.search(cr, uid, patient_domain, context=context)
        except_if(not patient_id, msg="Patient doesn't exist! Data: %s" % patient_domain)
        if vals_copy.get('title'):
            title_pool = self.pool['res.partner.title']
            titles = title_pool.read(cr, uid, title_pool.search(cr, uid, [], context=context), ['id', 'name'], context=context)
            title_id = False
            for t in titles:
                if t['name'].replace('.', '').lower() == vals_copy.get('title').replace('.', '').lower():
                    title_id = t['id']
                    break
            if not title_id:
                title_id = title_pool.create(cr, uid, {'name': vals_copy.get('title')})
            vals_copy.update({'title': title_id})
        vals_copy.update({'patient_id': patient_id[0], 'other_identifier': hospital_number, 'patient_identifier': nhs_number})
        return super(nh_clinical_adt_patient_update, self).submit(cr, uid, activity_id, vals_copy, context)
    
    def complete(self, cr, uid, activity_id, context=None): 
        res = {}
        activity_pool = self.pool['nh.activity']
        update_activity = activity_pool.browse(cr, uid, activity_id, context=context)
        patient_pool = self.pool['nh.clinical.patient']
        vals = {
            'title': update_activity.data_ref.title.id,
            'patient_identifier': update_activity.data_ref.patient_identifier,
            'other_identifier': update_activity.data_ref.other_identifier,
            'family_name': update_activity.data_ref.family_name,
            'given_name': update_activity.data_ref.given_name,
            'middle_names': update_activity.data_ref.middle_names,
            'dob': update_activity.data_ref.dob,
            'gender': update_activity.data_ref.gender,
            'sex': update_activity.data_ref.sex
        }
        res = patient_pool.write(cr, uid, update_activity.data_ref.patient_id.id, vals, context=context)
        super(nh_clinical_adt_patient_update, self).complete(cr, uid, activity_id, context)
        return res       


class nh_clinical_adt_spell_update(orm.Model):
    """
    Update patient spell information.
    """
    _name = 'nh.clinical.adt.spell.update'
    _inherit = ['nh.activity.data']
    _description = 'ADT Spell Update'
    _columns = {
        'suggested_location_id': fields.many2one('nh.clinical.location', 'Suggested Location', help="Location suggested by ADT for placement. Usually ward."),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS', required=True),
        'location': fields.text('Location'),
        'code': fields.text("Code"),
        'start_date': fields.datetime("ADT Start Date"),
        'other_identifier': fields.text("Other Identifier"),
        'doctors': fields.text("Doctors"),
        'ref_doctor_ids': fields.many2many('nh.clinical.doctor', 'ref_doctor_update_rel', 'spell_update_id', 'doctor_id', "Referring Doctors"),
        'con_doctor_ids': fields.many2many('nh.clinical.doctor', 'con_doctor_update_rel', 'spell_update_id', 'doctor_id', "Consulting Doctors")
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        res = {}
        user = self.pool['res.users'].browse(cr, uid, uid, context)
        except_if(not user.pos_id or not user.pos_id.location_id, msg="POS location is not set for user.login = %s!" % user.login)
        vals_copy = vals.copy()
        # location validation
        location_pool = self.pool['nh.clinical.location']
        suggested_location_id = location_pool.search(cr, SUPERUSER_ID, [('code', '=', vals['location']), ('id', 'child_of', user.pos_id.location_id.id)], context=context)
        if not suggested_location_id:
            _logger.warn("ADT suggested_location '%s' not found! Will automatically create one" % vals['location'])
            location_pool = self.pool['nh.clinical.location']
            suggested_location_id = location_pool.create(cr, uid, {
                'name': vals['location'],
                'code': vals['location'],
                'pos_id': user.pos_id.id,
                'type': 'poc',
                'usage': 'ward'
            }, context=context)
        else:
            suggested_location_id = suggested_location_id[0]
        vals_copy.update({'suggested_location_id': suggested_location_id})
        # patient validation
        patient_pool = self.pool['nh.clinical.patient']
        patient_id = patient_pool.search(cr, SUPERUSER_ID, [('other_identifier', '=', vals['other_identifier'])])
        except_if(not patient_id, msg="Patient not found!")
        if len(patient_id) > 1:
            _logger.warn("More than one patient found with 'other_identifier' = %s! Passed patient_id = %s"
                                    % (vals['other_identifier'], patient_id[0]))
        patient_id = patient_id[0]
        vals_copy.update({'patient_id': patient_id, 'pos_id': user.pos_id.id})
        # doctors
        if vals.get('doctors'):
            try:
                doctors = eval(str(vals['doctors']))
                ref_doctor_ids = []
                con_doctor_ids = []
                doctor_pool = self.pool['nh.clinical.doctor']
                for d in doctors:
                    doctor_id = doctor_pool.search(cr, uid, [['code', '=', d.get('code')]], context=context)
                    if not doctor_id:
                        title_id = False
                        if d.get('title'):
                            d['title'] = d['title'].strip()
                            title_pool = self.pool['res.partner.title']
                            title_id = title_pool.search(cr, uid, [['name', '=', d['title']]], context=context)
                            title_id = title_id[0] if title_id else title_pool.create(cr, uid, {'name': d['title']}, context=context)
                        data = {
                                'name': "%s, %s" % (d['family_name'], d['given_name']),
                                'title': title_id,
                                'code': d.get('code'),
                                'gender': d.get('gender'),
                                'gmc': d.get('gmc')
                                }
                        doctor_id = doctor_pool.create(cr, uid, data, context=context)
                    else:
                        if doctor_id > 1:
                            _logger.warn("More than one doctor found with code '%s' passed id=%s" % (d.get('code'), doctor_id[0]))
                        doctor_id = doctor_id[0]
                    ref_doctor_ids.append(doctor_id) if d['type'] == 'r' else con_doctor_ids.append(doctor_id)
                ref_doctor_ids and vals_copy.update({'ref_doctor_ids': [[6, False, ref_doctor_ids]]})
                con_doctor_ids and vals_copy.update({'con_doctor_ids': [[6, False, con_doctor_ids]]})
            except:
                _logger.warn("Can't evaluate 'doctors': %s" % (vals['doctors']))
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)

        super(nh_clinical_adt_spell_update, self).submit(cr, uid, activity_id, vals_copy, context=context)
        self.write(cr, uid, activity.data_ref.id, vals_copy, context=context)
        return res

    def complete(self, cr, uid, activity_id, context=None):
        super(nh_clinical_adt_spell_update, self).complete(cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        api_pool = self.pool['nh.clinical.api']
        update_activity = activity_pool.browse(cr, SUPERUSER_ID, activity_id, context=context)
        spell_activity_id = api_pool.get_patient_spell_activity_id(cr, SUPERUSER_ID, update_activity.data_ref.patient_id.id, context=context)
        except_if(not spell_activity_id, msg="Spell not found!")
        spell_activity = activity_pool.browse(cr, SUPERUSER_ID, spell_activity_id, context=context)
        data = {
            'con_doctor_ids': [[6, False, [d.id for d in update_activity.data_ref.con_doctor_ids]]],
            'ref_doctor_ids': [[6, False, [d.id for d in update_activity.data_ref.ref_doctor_ids]]],
            'location_id': update_activity.data_ref.pos_id.lot_admission_id.id,
            'code': update_activity.data_ref.code,
            'start_date': update_activity.data_ref.start_date if update_activity.data_ref.start_date < spell_activity.data_ref.start_date else spell_activity.data_ref.start_date
        }
        res = activity_pool.submit(cr, uid, spell_activity_id, data, context=context)
        activity_pool.write(cr, SUPERUSER_ID, activity_id, {'parent_id': spell_activity_id})
        # patient move
        move_pool = self.pool['nh.clinical.patient.move']
        move_activity_id = move_pool.create_activity(cr, SUPERUSER_ID,
            {'parent_id': spell_activity_id, 'creator_id': activity_id},
            {'patient_id': update_activity.data_ref.patient_id.id,
             'location_id': update_activity.data_ref.suggested_location_id.id},
            context=context)
        activity_pool.complete(cr, SUPERUSER_ID, move_activity_id, context)
        # trigger policy activities
        self.trigger_policy(cr, uid, activity_id, location_id=update_activity.data_ref.suggested_location_id.id, context=context)
        return res


class nh_clinical_adt_patient_cancel_discharge(orm.Model):
    """
    Cancels the last patient discharge. The spell will be reopened. This will fail if the patient has already been
    admitted again.
    """
    _name = 'nh.clinical.adt.patient.cancel_discharge'
    _inherit = ['nh.activity.data']
    _description = 'ADT Cancel Patient Discharge'
    _columns = {
        'other_identifier': fields.text('otherId', required=True),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS', required=True),
        'last_location_id': fields.many2one('nh.clinical.location', 'Last location'),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        activity_pool = self.pool['nh.activity']
        user = self.pool['res.users'].browse(cr, uid, uid, context)
        except_if(not user.pos_id or not user.pos_id.location_id, msg="POS location is not set for user.login = %s!" % user.login)
        patient_pool = self.pool['nh.clinical.patient']
        patient_id = patient_pool.search(cr, SUPERUSER_ID, [('other_identifier', '=', vals['other_identifier'])])
        except_if(not patient_id, msg="Patient not found!")
        if len(patient_id) > 1:
            _logger.warn("More than one patient found with 'other_identifier' = %s! Passed patient_id = %s"
                                    % (vals['other_identifier'], patient_id[0]))
        patient_id = patient_id[0]
        domain = [('data_model', '=', 'nh.clinical.patient.move'),
                  ('state', '=', 'completed'),
                  ('patient_id', '=', patient_id)]
        move_activity_ids = activity_pool.search(cr, uid, domain, order='date_terminated desc, sequence desc', context=context)
        move_activity = activity_pool.browse(cr, uid, move_activity_ids[1], context=context)
        vals_copy = vals.copy()
        if move_activity.location_id.type == 'poc':
            last_location_id = move_activity.location_id.id
        else:
            domain = [('state', '=', 'completed'),
                      ('patient_id', '=', patient_id),
                      ('data_model', 'in', ['nh.clinical.adt.patient.admit', 'nh.clinical.adt.spell.update',
                                            'nh.clinical.adt.patient.transfer', 'nh.clinical.adt.patient.cancel_transfer'])]
            op_activity_ids = activity_pool.search(cr, uid, domain, order='date_terminated desc, sequence desc', context=context)
            latest_op = activity_pool.browse(cr, uid, op_activity_ids[0], context=context)
            if latest_op.data_model in ['nh.clinical.adt.patient.admit', 'nh.clinical.adt.spell.update']:
                last_location_id = latest_op.data_ref.suggested_location_id.id
            elif latest_op.data_model == 'nh.clinical.adt.patient.cancel_transfer':
                last_location_id = latest_op.data_ref.last_location_id.id
            else:
                last_location_id = latest_op.data_ref.location_id.id
        vals_copy.update({'pos_id': user.pos_id.id, 'patient_id': patient_id, 'last_location_id': last_location_id})
        res = super(nh_clinical_adt_patient_cancel_discharge, self).submit(cr, uid, activity_id, vals_copy, context)
        return res

    def complete(self, cr, uid, activity_id, context=None):
        activity_pool = self.pool['nh.activity']
        api_pool = self.pool['nh.clinical.api']
        move_pool = self.pool['nh.clinical.patient.move']
        res = {}
        cancel_activity = activity_pool.browse(cr, SUPERUSER_ID, activity_id, context=context)
        patient_id = cancel_activity.data_ref.patient_id.id
        spell_activity_id = api_pool.activity_map(cr, uid, patient_ids=[patient_id], 
                                                  data_models=['nh.clinical.spell'], states=['started'])
        except_if(spell_activity_id, msg="Patient was not discharged or was admitted again!")
        
        super(nh_clinical_adt_patient_cancel_discharge, self).complete(cr, uid, activity_id, context=context)

        cancel_activity = activity_pool.browse(cr, SUPERUSER_ID, activity_id, context=context)
        domain = [('data_model', '=', 'nh.clinical.adt.patient.discharge'),
                  ('state', '=', 'completed'),
                  ('patient_id', '=', cancel_activity.data_ref.patient_id.id)]
        last_discharge_activity_id = activity_pool.search(cr, uid, domain, order='date_terminated desc, sequence desc', context=context)
        except_if(not last_discharge_activity_id, msg='Patient was not discharged!')
        spell_activity_id = api_pool.activity_map(cr, uid, patient_ids=[patient_id],
                                                  data_models=['nh.clinical.spell'], states=['completed']).keys()[0]

        res[self._name] = activity_pool.write(cr, uid, spell_activity_id, {'state': 'started'}, context=context)
        if cancel_activity.data_ref.last_location_id.usage == 'bed':
            if cancel_activity.data_ref.last_location_id.is_available:
                move_activity_id = move_pool.create_activity(cr, SUPERUSER_ID,
                    {'parent_id': spell_activity_id, 'creator_id': activity_id},
                    {'patient_id': cancel_activity.data_ref.patient_id.id,
                     'location_id': cancel_activity.data_ref.last_location_id.id},
                    context=context)
                res[move_pool._name] = move_activity_id
                activity_pool.complete(cr, SUPERUSER_ID, move_activity_id, context)
            else:
                move_activity_id = move_pool.create_activity(cr, SUPERUSER_ID,
                    {'parent_id': spell_activity_id, 'creator_id': activity_id},
                    {'patient_id': cancel_activity.data_ref.patient_id.id,
                     'location_id': cancel_activity.data_ref.last_location_id.id},
                    context=context)
                res[move_pool._name] = move_activity_id
                activity_pool.complete(cr, SUPERUSER_ID, move_activity_id, context)
                # trigger policy activities
                self.trigger_policy(cr, uid, activity_id, location_id=cancel_activity.data_ref.last_location_id.parent_id.id, context=context)
        else:
            move_activity_id = move_pool.create_activity(cr, SUPERUSER_ID,
                {'parent_id': spell_activity_id, 'creator_id': activity_id},
                {'patient_id': cancel_activity.data_ref.patient_id.id,
                 'location_id': cancel_activity.data_ref.last_location_id.id},
                context=context)
            res[move_pool._name] = move_activity_id
            activity_pool.complete(cr, SUPERUSER_ID, move_activity_id, context)
            # trigger policy activities
            self.write(cr, uid, cancel_activity.data_ref.id, {'last_location_id': cancel_activity.data_ref.last_location_id.child_ids[0].id}, context=context)
            self.trigger_policy(cr, uid, activity_id, location_id=cancel_activity.data_ref.last_location_id.id, context=context)
            self.write(cr, uid, cancel_activity.data_ref.id, {'last_location_id': cancel_activity.data_ref.last_location_id.id}, context=context)
        return res


class nh_clinical_adt_patient_cancel_transfer(orm.Model):
    """
    Cancels the last patient transfer. Effectively moving the patient back to the origin location.
    """
    _name = 'nh.clinical.adt.patient.cancel_transfer'
    _inherit = ['nh.activity.data']
    _description = 'ADT Cancel Patient Transfer'
    _columns = {
        'other_identifier': fields.text('otherId', required=True),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
        'last_location_id': fields.many2one('nh.clinical.location', 'Last Location')
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        activity_pool = self.pool['nh.activity']
        user = self.pool['res.users'].browse(cr, uid, uid, context)
        except_if(not user.pos_id or not user.pos_id.location_id, msg="POS location is not set for user.login = %s!" % user.login)
        patient_pool = self.pool['nh.clinical.patient']
        patient_id = patient_pool.search(cr, SUPERUSER_ID, [('other_identifier', '=', vals['other_identifier'])])
        except_if(not patient_id, msg="Patient not found!")
        if len(patient_id) > 1:
            _logger.warn("More than one patient found with 'other_identifier' = %s! Passed patient_id = %s"
                                    % (vals['other_identifier'], patient_id[0]))
        patient_id = patient_id[0]
        domain = [('data_model', '=', 'nh.clinical.adt.patient.transfer'),
                  ('state', '=', 'completed'),
                  ('patient_id', '=', patient_id)]
        transfer_activity_ids = activity_pool.search(cr, uid, domain, order='date_terminated desc, sequence desc', context=context)
        except_if(not transfer_activity_ids, msg='Patient was not transfered!')
        transfer_activity = activity_pool.browse(cr, uid, transfer_activity_ids[0], context=context)
        vals_copy = vals.copy()
        vals_copy.update({'patient_id': patient_id, 'last_location_id': transfer_activity.data_ref.from_location_id.id})
        res = super(nh_clinical_adt_patient_cancel_transfer, self).submit(cr, uid, activity_id, vals_copy, context)
        return res

    def complete(self, cr, uid, activity_id, context=None):
        res = {}
        super(nh_clinical_adt_patient_cancel_transfer, self).complete(cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        api_pool = self.pool['nh.clinical.api']
        move_pool = self.pool['nh.clinical.patient.move']
        cancel_activity = activity_pool.browse(cr, SUPERUSER_ID, activity_id, context=context)

        # patient move
        spell_activity_id = api_pool.get_patient_spell_activity_id(cr, SUPERUSER_ID, cancel_activity.data_ref.patient_id.id, context=context)
        except_if(not spell_activity_id, msg="Spell not found!")
        move_activity_id = move_pool.create_activity(cr, SUPERUSER_ID,{
            'parent_id': spell_activity_id,
            'creator_id': activity_id
        }, {
            'patient_id': cancel_activity.data_ref.patient_id.id,
            'location_id': cancel_activity.data_ref.last_location_id.id},
            context=context)
        res[move_pool._name] = move_activity_id
        activity_pool.complete(cr, SUPERUSER_ID, move_activity_id, context)
        # trigger policy activities
        self.trigger_policy(cr, uid, activity_id, location_id=cancel_activity.data_ref.last_location_id.id, context=context)
        return res