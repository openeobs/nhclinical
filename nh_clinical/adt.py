# -*- coding: utf-8 -*-
"""
``adt.py`` defines a set of activity types to deal with patient
management systems operations.
"""

from datetime import datetime as dt
import logging

from openerp.osv import orm, fields, osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class nh_clinical_adt_patient_register(orm.Model):
    """
    Represents the patient register operation in the patient management
    system. (A28 Message)
    """
    _name = 'nh.clinical.adt.patient.register'
    _inherit = ['nh.activity.data']   
    _description = 'ADT Patient Register'

    _gender = [['BOTH', 'Both'], ['F', 'Female'], ['I', 'Intermediate'],
               ['M', 'Male'], ['NSP', 'Not Specified'], ['U', 'Unknown']]
    _ethnicity = [
        ['A', 'White - British'], ['B', 'White - Irish'], ['C', 'White - Other background'],
        ['D', 'Mixed - White and Black Caribbean'], ['E', 'Mixed - White and Black African'],
        ['F', 'Mixed - White and Asian'], ['G', 'Mixed - Other background'], ['H', 'Asian - Indian'],
        ['J', 'Asian - Pakistani'], ['K', 'Asian - Bangladeshi'], ['L', 'Asian - Other background'],
        ['M', 'Black - Caribbean'], ['N', 'Black - African'], ['P', 'Black - Other background'], ['R', 'Chinese'],
        ['S', 'Other ethnic group'], ['Z', 'Not stated']
    ]

    _columns = { 
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient'),
        'patient_identifier': fields.char('NHS Number', size=10),
        'other_identifier': fields.char('Hospital Number', size=50),
        'family_name': fields.char('Last Name', size=200),
        'given_name': fields.char('First Name', size=200),
        'middle_names': fields.char('Middle Names', size=200),
        'dob': fields.datetime('Date of Birth'),
        'gender': fields.selection(_gender, string='Gender'),
        'sex': fields.selection(_gender, string='Sex'),
        'ethnicity': fields.selection(_ethnicity, string='Ethnicity'),
        'title': fields.many2one('res.partner.title', 'Title')
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the patient data is correct and then calls
        :meth:`submit<activity.nh_activity.submit>`.

        :returns: ``True``
        :rtype: bool
        """
        data = vals.copy()
        patient_pool = self.pool['nh.clinical.patient']
        patient_pool.check_data(cr, uid, data, context=context)
        return super(nh_clinical_adt_patient_register, self).submit(cr, uid, activity_id, data, context)
    
    def complete(self, cr, uid, activity_id, context=None):
        """
        Creates a new instance of
        :mod:`patient<base.nh_clinical_patient>` and
        then calls :meth:`complete<activity.nh_activity.complete>`.

        :returns: :mod:`patient<base.nh_clinical_patient>` id
        :rtype: int
        """
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        patient_pool = self.pool['nh.clinical.patient']
        vals = {
            'title': activity.data_ref.title.id,
            'patient_identifier': activity.data_ref.patient_identifier,
            'other_identifier': activity.data_ref.other_identifier,
            'family_name': activity.data_ref.family_name,
            'given_name': activity.data_ref.given_name,
            'middle_names': activity.data_ref.middle_names,
            'dob': activity.data_ref.dob,
            'gender': activity.data_ref.gender,
            'sex': activity.data_ref.sex,
            'ethnicity': activity.data_ref.ethnicity
        }
        patient_id = patient_pool.create(cr, uid, vals, context)
        activity_pool.write(cr, uid, activity_id, {'patient_id': patient_id}, context=context)
        self.write(cr, uid, activity.data_ref.id, {'patient_id': patient_id}, context=context)
        super(nh_clinical_adt_patient_register, self).complete(cr, uid, activity_id, context)
        return patient_id


class nh_clinical_adt_patient_update(orm.Model):
    """
    Represents the patient update operation in the patient management
    system. (A31 Message)
    """

    _name = 'nh.clinical.adt.patient.update'
    _inherit = ['nh.activity.data']
    _description = 'ADT Patient Update'

    _gender = [['BOTH', 'Both'], ['F', 'Female'], ['I', 'Intermediate'],
               ['M', 'Male'], ['NSP', 'Not Specified'], ['U', 'Unknown']]
    _ethnicity = [
        ['A', 'White - British'], ['B', 'White - Irish'], ['C', 'White - Other background'],
        ['D', 'Mixed - White and Black Caribbean'], ['E', 'Mixed - White and Black African'],
        ['F', 'Mixed - White and Asian'], ['G', 'Mixed - Other background'], ['H', 'Asian - Indian'],
        ['J', 'Asian - Pakistani'], ['K', 'Asian - Bangladeshi'], ['L', 'Asian - Other background'],
        ['M', 'Black - Caribbean'], ['N', 'Black - African'], ['P', 'Black - Other background'], ['R', 'Chinese'],
        ['S', 'Other ethnic group'], ['Z', 'Not stated']
    ]

    _columns = {
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
        'patient_identifier': fields.char('NHS Number', size=10),
        'other_identifier': fields.char('Hospital Number', size=50),
        'family_name': fields.char('Last Name', size=200),
        'given_name': fields.char('First Name', size=200),
        'middle_names': fields.char('Middle Names', size=200),
        'dob': fields.datetime('Date of Birth'),
        'gender': fields.selection(_gender, string='Gender'),
        'sex': fields.selection(_gender, string='Sex'),
        'ethnicity': fields.selection(_ethnicity, string='Ethnicity'),
        'title': fields.many2one('res.partner.title', 'Title')
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the patient data is correct and then calls
        :meth:`submit<activity.nh_activity.submit>`.

        :returns: ``True``
        :rtype: bool
        """
        data = vals.copy()
        patient_pool = self.pool['nh.clinical.patient']
        patient_pool.check_data(cr, uid, data, create=False, context=context)
        return super(nh_clinical_adt_patient_update, self).submit(cr, uid, activity_id, data, context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Overwrites the target :mod:`patient<base.nh_clinical_patient>`
        instance information and then calls
        :meth:`complete<activity.nh_activity.complete>`.

        :returns: ``True``
        :rtype: bool
        """
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        patient_pool = self.pool['nh.clinical.patient']
        vals = {
            'title': activity.data_ref.title.id,
            'patient_identifier': activity.data_ref.patient_identifier,
            'other_identifier': activity.data_ref.other_identifier,
            'family_name': activity.data_ref.family_name,
            'given_name': activity.data_ref.given_name,
            'middle_names': activity.data_ref.middle_names,
            'dob': activity.data_ref.dob,
            'gender': activity.data_ref.gender,
            'sex': activity.data_ref.sex,
            'ethnicity': activity.data_ref.ethnicity
        }
        res = patient_pool.write(cr, uid, activity.data_ref.patient_id.id, vals, context=context)
        super(nh_clinical_adt_patient_update, self).complete(cr, uid, activity_id, context)
        return res


class nh_clinical_adt_patient_admit(orm.Model):
    """
    Represents the patient admission operation in the patient management
    system. (A01 Message)

    Consulting and referring doctors are expected in the submitted
    values in the following format::

        [...
            {
                'type': 'c' or 'r', 'code': 'code_string,
                'title': 'Mr', 'given_name': 'John',
                'family_name': 'Smith'
            }...
        ]
       
    If doctor doesn't exist, then a partner is created (but no user is
    created).
    """
    
    _name = 'nh.clinical.adt.patient.admit'
    _inherit = ['nh.activity.data']      
    _description = 'ADT Patient Admit'    
    _columns = {
        'location_id': fields.many2one('nh.clinical.location', 'Admission Location'),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS', required=True),
        'location': fields.char('Location', size=256),
        'code': fields.char("Code", size=256),
        'start_date': fields.datetime("Admission Date"),
        'other_identifier': fields.char('Hospital Number', size=100),
        'patient_identifier': fields.char('NHS Number', size=100),
        'doctors': fields.text("Doctors")
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data and then calls
        :meth:`submit<activity.nh_activity.submit>`.

        If a :mod:`location<base.nh_clinical_location>` of `ward` usage
        with the provided code does not exist, it will create a new one.

        Due to this behaviour the user submitting the data must be
        related to a :mod:`point of service<base.nh_clinical_pos>`
        linked to a valid :mod:`location<base.nh_clinical_location>`
        instance of `pos` type, as new Wards will need to be assigned to
        a point of service.

        :returns: ``True``
        :rtype: bool
        """
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        if not user.pos_id or not user.pos_id.location_id:
            raise osv.except_osv('POS Missing Error!', "POS location is not set for user.login = %s!" % user.login)
        if not vals.get('location'):
            raise osv.except_osv('Admission Error!', 'Location must be set for admission!')
        if not vals.get('other_identifier'):
            if not vals.get('patient_identifier'):
                raise osv.except_osv('Admission Error!', 'Patient must be set for admission!')
        location_pool = self.pool['nh.clinical.location']
        location_id = location_pool.get_by_code(cr, uid, vals['location'], auto_create=True, context=context)
        patient_pool = self.pool['nh.clinical.patient']
        if vals.get('other_identifier'):
            patient_pool.check_hospital_number(cr, uid, vals['other_identifier'], exception='False', context=context)
            patient_id = patient_pool.search(cr, uid, [['other_identifier', '=', vals['other_identifier']]],
                                             context=context)[0]
        else:
            patient_pool.check_nhs_number(cr, uid, vals['patient_identifier'], exception='False', context=context)
            patient_id = patient_pool.search(cr, uid, [['patient_identifier', '=', vals['patient_identifier']]],
                                             context=context)[0]
        data = vals.copy()
        data.update({
            'location_id': location_id,
            'patient_id': patient_id,
            'pos_id': user.pos_id.id
        })
        return super(nh_clinical_adt_patient_admit, self).submit(cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        creates and completes a new
        :mod:`admission<operations.nh_clinical_patient_admission>` to
        the provided location.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_adt_patient_admit, self).complete(cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        admission_pool = self.pool['nh.clinical.patient.admission']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        admission_data = {
            'pos_id': activity.data_ref.pos_id.id,
            'patient_id': activity.data_ref.patient_id.id,
            'location_id': activity.data_ref.location_id.id,
            'code': activity.data_ref.code,
            'start_date': activity.data_ref.start_date
        }
        if activity.data_ref.doctors:
            doctor_pool = self.pool['nh.clinical.doctor']
            admission_data.update({'doctors': activity.data_ref.doctors})
            doctor_pool.evaluate_doctors_dict(cr, uid, admission_data, context=context)
            del admission_data['doctors']
        admission_id = admission_pool.create_activity(cr, uid, {'creator_id': activity_id}, admission_data,
                                                      context=context)
        activity_pool.complete(cr, uid, admission_id, context=context)
        spell_id = activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.spell'], ['creator_id', '=', admission_id]], context=context)[0]
        activity_pool.write(cr, SUPERUSER_ID, activity_id, {'parent_id': spell_id})
        return res  

    
class nh_clinical_adt_patient_cancel_admit(orm.Model):
    """
    Represents the cancel admission operation in the patient management
    system. (A11 Message)
    """
    _name = 'nh.clinical.adt.patient.cancel_admit'
    _inherit = ['nh.activity.data']  
    _description = 'ADT Cancel Patient Admit'    
    _columns = {
        'other_identifier': fields.char('Hospital Number', size=50, required=True),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
        'admission_id': fields.many2one('nh.activity', 'Admission Activity')
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data is correct, finding the last completed
        instance of
        :mod:`admission<operations.nh_clinical_patient_admission>`
        and then calls :meth:`submit<activity.nh_activity.submit>`.

        :returns: ``True``
        :rtype: bool
        """
        if not vals.get('other_identifier'):
            raise osv.except_osv('Cancel Admit Error!', 'Patient must be set!')
        patient_pool = self.pool['nh.clinical.patient']
        patient_pool.check_hospital_number(cr, uid, vals['other_identifier'], exception='False', context=context)
        patient_id = patient_pool.search(cr, uid, [['other_identifier', '=', vals['other_identifier']]],
                                         context=context)[0]
        spell_pool = self.pool['nh.clinical.spell']
        activity_pool = self.pool['nh.activity']
        spell_id = spell_pool.get_by_patient_id(cr, uid, patient_id, exception='False', context=context)
        spell = spell_pool.browse(cr, uid, spell_id, context=context)
        activity_pool.write(cr, uid, activity_id, {'parent_id': spell.activity_id.id}, context=context)
        admission_pool = self.pool['nh.clinical.patient.admission']
        admission_id = admission_pool.get_last(cr, uid, patient_id, exception='False', context=context)
        data = vals.copy()
        data.update({'patient_id': patient_id, 'admission_id': admission_id})
        return super(nh_clinical_adt_patient_cancel_admit, self).submit(cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        cancels the last `completed`
        :mod:`admission<operations.nh_clinical_patient_admission>` for
        the provided patient.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_adt_patient_cancel_admit, self).complete(cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        activity_pool.cancel(cr, uid, activity.data_ref.admission_id.id, context=context)
        return res


class nh_clinical_adt_patient_discharge(orm.Model):
    """
    Represents the patient discharge operation in the patient management
    system. (A03 Message)
    """
    _name = 'nh.clinical.adt.patient.discharge'
    _inherit = ['nh.activity.data']  
    _description = 'ADT Patient Discharge'
    _columns = {
        'other_identifier': fields.char('Hospital Number', size=100),
        'patient_identifier': fields.char('NHS Number', size=100),
        'location': fields.char('Pre-Discharge Location', size=256),
        'location_id': fields.many2one('nh.clinical.location', 'Pre-Discharge Location'),
        'discharge_date': fields.datetime('Discharge Date'),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True)
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data and then calls
        :meth:`submit<activity.nh_activity.submit>`.

        Creates a new :mod:`spell<spell.nh_clinical_spell>` for the
        provided patient if there is not an open instance related to it.
        Requires the user to be linked to a
        :mod:`point of service<base.nh_clinical_pos>` due to similar
        behaviour as the admission in this particular scenario.

        :returns: ``True``
        :rtype: bool
        """
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        if not user.pos_id or not user.pos_id.location_id:
            raise osv.except_osv('POS Missing Error!', "POS location is not set for user.login = %s!" % user.login)
        if not vals.get('other_identifier'):
            if not vals.get('patient_identifier'):
                raise osv.except_osv('Discharge Error!', 'Patient must be set!')
        data = vals.copy()
        patient_pool = self.pool['nh.clinical.patient']
        if vals.get('other_identifier'):
            patient_pool.check_hospital_number(cr, uid, vals['other_identifier'], exception='False', context=context)
            patient_id = patient_pool.search(cr, uid, [['other_identifier', '=', vals['other_identifier']]],
                                             context=context)[0]
        else:
            patient_pool.check_nhs_number(cr, uid, vals['patient_identifier'], exception='False', context=context)
            patient_id = patient_pool.search(cr, uid, [['patient_identifier', '=', vals['patient_identifier']]],
                                             context=context)[0]
        discharge_date = vals.get('discharge_date') if vals.get('discharge_date') else dt.now().strftime(DTF)
        spell_pool = self.pool['nh.clinical.spell']
        activity_pool = self.pool['nh.activity']
        spell_id = spell_pool.get_by_patient_id(cr, uid, patient_id, context=context)
        if not spell_id:
            if not vals.get('location'):
                raise osv.except_osv('Discharge Error!', 'Missing location and patient is not admitted!')
            discharged = activity_pool.search(cr, uid, [['data_model', '=', 'nh.clinical.spell'],
                                              ['patient_id', '=', patient_id], ['state', '=', 'completed']],
                                              context=context)
            if discharged:
                raise osv.except_osv('Discharge Error!', 'Patient is already discharged!')
            _logger.warn("Patient admitted from a discharge call!")
            location_pool = self.pool['nh.clinical.location']
            location_id = location_pool.get_by_code(cr, uid, vals['location'], auto_create=True, context=context)
            data.update({'location_id': location_id})
            admission_pool = self.pool['nh.clinical.patient.admission']
            admission_data = {
                'pos_id': user.pos_id.id,
                'patient_id': patient_id,
                'location_id': location_id,
            }
            admission_id = admission_pool.create_activity(cr, uid, {'creator_id': activity_id}, admission_data,
                                                          context=context)
            activity_pool.complete(cr, uid, admission_id, context=context)
            spell_id = spell_pool.get_by_patient_id(cr, uid, patient_id, exception='False', context=context)
        spell = spell_pool.browse(cr, uid, spell_id, context=context)
        data.update({'patient_id': patient_id, 'discharge_date': discharge_date})
        activity_pool.write(cr, uid, activity_id, {'parent_id': spell.activity_id.id}, context=context)
        return super(nh_clinical_adt_patient_discharge, self).submit(cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        creates and completes a new
        :mod:`discharge<operations.nh_clinical_patient_discharge>` for
        the provided patient.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_adt_patient_discharge, self).complete(cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        discharge_pool = self.pool['nh.clinical.patient.discharge']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        discharge_data = {
            'patient_id': activity.data_ref.patient_id.id,
            'discharge_date': activity.data_ref.discharge_date
        }
        discharge_id = discharge_pool.create_activity(cr, uid, {'creator_id': activity_id}, discharge_data,
                                                      context=context)
        activity_pool.complete(cr, uid, discharge_id, context=context)
        return res


class nh_clinical_adt_patient_cancel_discharge(orm.Model):
    """
    Represents the cancel discharge operation in the patient management
    system. (A13 Message)
    """
    _name = 'nh.clinical.adt.patient.cancel_discharge'
    _inherit = ['nh.activity.data']
    _description = 'ADT Cancel Patient Discharge'
    _columns = {
        'other_identifier': fields.char('Hospital Number', size=50, required=True),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
        'discharge_id': fields.many2one('nh.activity', 'Discharge Activity')
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data is correct, finding the last
        `completed` instance of
        :mod:`discharge<operations.nh_clinical_patient_discharge>`
        and then calls :meth:`submit<activity.nh_activity.submit>`.

        :returns: ``True``
        :rtype: bool
        """
        if not vals.get('other_identifier'):
            raise osv.except_osv('Cancel Discharge Error!', 'Patient must be set!')
        patient_pool = self.pool['nh.clinical.patient']
        patient_pool.check_hospital_number(cr, uid, vals['other_identifier'], exception='False', context=context)
        patient_id = patient_pool.search(cr, uid, [['other_identifier', '=', vals['other_identifier']]],
                                         context=context)[0]
        discharge_pool = self.pool['nh.clinical.patient.discharge']
        discharge_id = discharge_pool.get_last(cr, uid, patient_id, exception='False', context=context)
        data = vals.copy()
        data.update({'patient_id': patient_id, 'discharge_id': discharge_id})
        return super(nh_clinical_adt_patient_cancel_discharge, self).submit(cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        cancels the last `completed`
        :mod:`discharge<operations.nh_clinical_patient_discharge>` for
        the provided patient.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_adt_patient_cancel_discharge, self).complete(cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        activity_pool.cancel(cr, uid, activity.data_ref.discharge_id.id, context=context)
        activity_pool.write(cr, uid, activity_id, {'parent_id': activity.data_ref.discharge_id.parent_id.id},
                            context=context)
        return res


class nh_clinical_adt_patient_transfer(orm.Model):
    """
    Represents the patient transfer operation in the patient management
    system. (A02 Message)
    """
    _name = 'nh.clinical.adt.patient.transfer'
    _inherit = ['nh.activity.data']
    _description = 'ADT Patient Transfer'      
    _columns = {
        'other_identifier': fields.char('Hospital Number', size=100),
        'patient_identifier': fields.char('NHS Number', size=100),
        'original_location': fields.char('Location of Origin', size=256),
        'origin_location_id': fields.many2one('nh.clinical.location', 'Origin Location'),
        'location': fields.char('Location', size=256),
        'location_id': fields.many2one('nh.clinical.location', 'Transfer Location'),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True)
    }
    
    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data and then calls
        :meth:`submit<activity.nh_activity.submit>`.

        Creates a new :mod:`spell<spell.nh_clinical_spell>` for the
        provided patient if there is not an open instance related to it
        and an origin location for the transfer was provided.
        Requires the user to be linked to a
        :mod:`point of service<base.nh_clinical_pos>` due to similar
        behaviour as the admission in this particular scenario.

        :returns: ``True``
        :rtype: bool
        """
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        if not user.pos_id or not user.pos_id.location_id:
            raise osv.except_osv('POS Missing Error!', "POS location is not set for user.login = %s!" % user.login)
        if not vals.get('location'):
            raise osv.except_osv('Transfer Error!', 'Location must be set for transfer!')
        if not vals.get('other_identifier'):
            if not vals.get('patient_identifier'):
                raise osv.except_osv('Transfer Error!', 'Patient must be set for transfer!')
        location_pool = self.pool['nh.clinical.location']
        location_id = location_pool.get_by_code(cr, uid, vals['location'], auto_create=True, context=context)
        olocation_id = location_pool.get_by_code(cr, uid, vals['original_location'], auto_create=True, context=context) \
            if vals.get('original_location') else False
        patient_pool = self.pool['nh.clinical.patient']
        if vals.get('other_identifier'):
            patient_pool.check_hospital_number(cr, uid, vals['other_identifier'], exception='False', context=context)
            patient_id = patient_pool.search(cr, uid, [['other_identifier', '=', vals['other_identifier']]],
                                             context=context)[0]
        else:
            patient_pool.check_nhs_number(cr, uid, vals['patient_identifier'], exception='False', context=context)
            patient_id = patient_pool.search(cr, uid, [['patient_identifier', '=', vals['patient_identifier']]],
                                             context=context)[0]
        spell_pool = self.pool['nh.clinical.spell']
        activity_pool = self.pool['nh.activity']
        spell_id = spell_pool.get_by_patient_id(cr, uid, patient_id, context=context)
        if not spell_id:
            if olocation_id:
                api = self.pool['nh.clinical.api']
                api.admit(cr, uid, vals['other_identifier'], {'location': vals['original_location']}, context=context)
                spell_id = spell_pool.get_by_patient_id(cr, uid, patient_id, context=context)
            else:
                raise osv.except_osv('Transfer Error!', 'Patient does not have an open spell. No origin location provided.')
        spell = spell_pool.browse(cr, uid, spell_id, context=context)
        activity_pool.write(cr, uid, activity_id, {'parent_id': spell.activity_id.id}, context=context)
        data = vals.copy()
        data.update({
            'location_id': location_id,
            'origin_location_id': olocation_id,
            'patient_id': patient_id
        })
        return super(nh_clinical_adt_patient_transfer, self).submit(cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        creates and completes a new
        :mod:`transfer<operations.nh_clinical_patient_transfer>` for the
        provided patient.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_adt_patient_transfer, self).complete(cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        transfer_pool = self.pool['nh.clinical.patient.transfer']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        transfer = activity.data_ref
        transfer_data = {
            'patient_id': transfer.patient_id.id,
            'location_id': transfer.location_id.id
        }
        transfer_id = transfer_pool.create_activity(cr, uid, {'creator_id': activity_id}, transfer_data,
                                                    context=context)
        activity_pool.complete(cr, uid, transfer_id, context=context)
        return res


class nh_clinical_adt_patient_cancel_transfer(orm.Model):
    """
    Represents the cancel transfer operation in the patient management
    system. (A12 Message)
    """
    _name = 'nh.clinical.adt.patient.cancel_transfer'
    _inherit = ['nh.activity.data']
    _description = 'ADT Cancel Patient Transfer'
    _columns = {
        'other_identifier': fields.char('Hospital Number', size=100),
        'patient_identifier': fields.char('NHS Number', size=100),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
        'transfer_id': fields.many2one('nh.activity', 'Transfer Activity')
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data is correct, finding the last
        `completed` instance of
        :mod:`transfer<operations.nh_clinical_patient_transfer>`
        and then calls :meth:`submit<activity.nh_activity.submit>`.

        :returns: ``True``
        :rtype: bool
        """
        if not vals.get('other_identifier'):
            raise osv.except_osv('Cancel Transfer Error!', 'Patient must be set!')
        patient_pool = self.pool['nh.clinical.patient']
        patient_pool.check_hospital_number(cr, uid, vals['other_identifier'], exception='False', context=context)
        patient_id = patient_pool.search(cr, uid, [['other_identifier', '=', vals['other_identifier']]],
                                         context=context)[0]
        transfer_pool = self.pool['nh.clinical.patient.transfer']
        transfer_id = transfer_pool.get_last(cr, uid, patient_id, exception='False', context=context)
        data = vals.copy()
        data.update({'patient_id': patient_id, 'transfer_id': transfer_id})
        return super(nh_clinical_adt_patient_cancel_transfer, self).submit(cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        cancels the last `completed`
        :mod:`transfer<operations.nh_clinical_patient_transfer>` for the
        provided patient.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_adt_patient_cancel_transfer, self).complete(cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        cancel = activity.data_ref
        activity_pool.cancel(cr, uid, cancel.transfer_id.id, context=context)
        activity_pool.write(cr, uid, activity_id, {'parent_id': cancel.transfer_id.parent_id.id},
                            context=context)
        return res


class nh_clinical_adt_spell_update(orm.Model):
    """
    Represents the admission update operation in the patient management
    system. (A08 Message)
    """
    _name = 'nh.clinical.adt.spell.update'
    _inherit = ['nh.activity.data']
    _description = 'ADT Spell Update'
    _columns = {
        'location_id': fields.many2one('nh.clinical.location', 'Admission Location'),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient', required=True),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS', required=True),
        'location': fields.char('Location', size=256),
        'code': fields.char("Code", size=256),
        'start_date': fields.datetime("Admission Date"),
        'other_identifier': fields.char('Hospital Number', size=100),
        'patient_identifier': fields.char('NHS Number', size=100),
        'doctors': fields.text("Doctors"),
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data and then calls
        :meth:`submit<activity.nh_activity.submit>`.

        If a :mod:`location<base.nh_clinical_location>` of `ward` usage
        with the provided code does not exist, it will create a new one.

        Due to this behaviour the user submitting the data must be
        related to a :mod:`point of service<base.nh_clinical_pos>`
        linked to a valid :mod:`location<base.nh_clinical_location>`
        instance of `pos` type, as new Wards will need to be assigned
        to a point of service.

        :returns: ``True``
        :rtype: bool
        """
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        if not user.pos_id or not user.pos_id.location_id:
            raise osv.except_osv('POS Missing Error!', "POS location is not set for user.login = %s!" % user.login)
        if not vals.get('location'):
            raise osv.except_osv('Update Error!', 'Location must be set for spell update!')
        if not vals.get('other_identifier'):
            if not vals.get('patient_identifier'):
                raise osv.except_osv('Update Error!', 'Patient must be set for spell update!')
        location_pool = self.pool['nh.clinical.location']
        location_id = location_pool.get_by_code(cr, uid, vals['location'], auto_create=True, context=context)
        patient_pool = self.pool['nh.clinical.patient']
        if vals.get('other_identifier'):
            patient_pool.check_hospital_number(cr, uid, vals['other_identifier'], exception='False', context=context)
            patient_id = patient_pool.search(cr, uid, [['other_identifier', '=', vals['other_identifier']]],
                                             context=context)[0]
        else:
            patient_pool.check_nhs_number(cr, uid, vals['patient_identifier'], exception='False', context=context)
            patient_id = patient_pool.search(cr, uid, [['patient_identifier', '=', vals['patient_identifier']]],
                                             context=context)[0]
        spell_pool = self.pool['nh.clinical.spell']
        activity_pool = self.pool['nh.activity']
        spell_id = spell_pool.get_by_patient_id(cr, uid, patient_id, context=context)
        if not spell_id:
            raise osv.except_osv('Update Error!', 'The patient does not have an open spell!')
        spell = spell_pool.browse(cr, uid, spell_id, context=context)
        activity_pool.write(cr, uid, activity_id, {'parent_id': spell.activity_id.id}, context=context)
        data = vals.copy()
        data.update({
            'location_id': location_id,
            'patient_id': patient_id,
            'pos_id': user.pos_id.id
        })
        return super(nh_clinical_adt_spell_update, self).submit(cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Overwrites the target :mod:`spell<spell.nh_clinical_spell>`
        information and then calls
        :meth:`complete<activity.nh_activity.complete>`.

        If location information needs to be updated a new instance of
        :mod:`movement<operations.nh_clinical_patient_move>` is created
        and completed.

        If the new location is located in a different Ward than the
        current spell location, a
        :meth:`policy trigger<activity.nh_activity_data.trigger_policy>`
        will be kicked off. As that is technically a transfer movement.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_adt_spell_update, self).complete(cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        update = activity.data_ref
        update_data = {
            'pos_id': update.pos_id.id,
            'code': update.code,
            'start_date': update.start_date
        }
        if update.doctors:
            doctor_pool = self.pool['nh.clinical.doctor']
            update_data.update({'doctors': update.doctors})
            doctor_pool.evaluate_doctors_dict(cr, uid, update_data, context=context)
            del update_data['doctors']
        else:
            update_data.update({'con_doctor_ids': [[5]], 'ref_doctor_ids': [[5]]})
        activity_pool.submit(cr, uid, activity.parent_id.id, update_data, context=context)
        location_pool = self.pool['nh.clinical.location']
        if not location_pool.is_child_of(cr, uid, activity.parent_id.location_id.id, update.location, context=context):
            move_pool = self.pool['nh.clinical.patient.move']
            move_activity_id = move_pool.create_activity(cr, SUPERUSER_ID, {
                'parent_id': activity.parent_id.id,
                'creator_id': activity_id
            }, {
                'patient_id': update.patient_id.id,
                'location_id': update.location_id.id
            }, context=context)
            activity_pool.complete(cr, SUPERUSER_ID, move_activity_id, context=context)
            # trigger transfer policy activities
            self.trigger_policy(cr, uid, activity_id, location_id=update.location_id.id, context=context)
        return res
        

class nh_clinical_adt_patient_merge(orm.Model):
    """
    Represents the patient merge operation in the patient management
    system. (A40 Message)
    Merges a patient into another patient making the resulting patient own all activities.
    """
    _name = 'nh.clinical.adt.patient.merge'
    _inherit = ['nh.activity.data'] 
    _description = 'ADT Patient Merge'
    _columns = {
        'from_identifier': fields.char('Source Identifier', size=100),
        'source_patient_id': fields.many2one('nh.clinical.patient', 'Source Patient'),
        'into_identifier': fields.char('Destination Identifier', size=100),        
        'dest_patient_id': fields.many2one('nh.clinical.patient', 'Destination Patient'),
    }
    
    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data and then calls
        :meth:`submit<activity.nh_activity.submit>`.

        :returns: ``True``
        :rtype: bool
        """
        patient_pool = self.pool['nh.clinical.patient']
        data = vals.copy()
        if data.get('from_identifier'):
            patient_pool.check_hospital_number(cr, uid, data['from_identifier'], exception='False', context=context)
            from_id = patient_pool.search(cr, uid, [('other_identifier', '=', data['from_identifier'])])[0]
            data.update({'source_patient_id': from_id})
        if data.get('into_identifier'):
            patient_pool.check_hospital_number(cr, uid, data['into_identifier'], exception='False', context=context)
            into_id = patient_pool.search(cr, uid, [('other_identifier', '=', data['into_identifier'])])[0]
            data.update({'dest_patient_id': into_id})
        return super(nh_clinical_adt_patient_merge, self).submit(cr, uid, activity_id, data, context=context)
        
    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        adds every piece of information that the source patient has and
        the destination patient lacks into the destination patient.

        The destination patient ends up being linked to all the
        :class:`activities<activity.nh_activity>` both patients were
        linked to.

        :returns: ``True``
        :rtype: bool
        """
        res = {}
        activity_pool = self.pool['nh.activity']
        merge_activity = activity_pool.browse(cr, SUPERUSER_ID, activity_id, context=context)
        if not merge_activity.data_ref.source_patient_id:
            raise osv.except_osv('Patient Merge Error!', "Source patient not found in submitted data!")
        if not merge_activity.data_ref.dest_patient_id:
            raise osv.except_osv('Patient Merge Error!', "Destination patient not found in submitted data!")
        super(nh_clinical_adt_patient_merge, self).complete(cr, uid, activity_id, context=context)        
        patient_pool = self.pool['nh.clinical.patient']
        from_id = merge_activity.data_ref.source_patient_id.id
        into_id = merge_activity.data_ref.dest_patient_id.id        
        # compare and combine data. may need new cursor to have the update in one transaction
        for model_name in self.pool.models.keys():
            model_pool = self.pool[model_name]
            if model_name.startswith("nh.clinical") and model_pool._auto and 'patient_id' in model_pool._columns.keys() \
                    and model_name != self._name and model_name != 'nh.clinical.notification' \
                    and model_name != 'nh.clinical.patient.observation':
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
        res['merge_into_update'] = patient_pool.write(cr, uid, into_id, vals_into, context=context)
        res['merge_from_deactivate'] = patient_pool.write(cr, uid, from_id, {'active': False}, context=context)
        activity_pool.write(cr, uid, activity_id, {'patient_id': into_id}, context=context)
        return res