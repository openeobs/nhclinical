# -*- coding: utf-8 -*-
import logging

from openerp.osv import orm, osv
_logger = logging.getLogger(__name__)


class nh_clinical_api(orm.AbstractModel):
    _name = 'nh.clinical.api'

    def update(self, cr, uid, hospital_number, data, context=None):
        """
        Update patient information
        """
        activity_pool = self.pool['nh.activity']
        patient_pool = self.pool['nh.clinical.patient']
        update_pool = self.pool['nh.clinical.adt.patient.update']
        if not patient_pool.check_hospital_number(cr, uid, hospital_number, context=context):
            nhs_data = data.copy()
            nhs_data['other_identifier'] = hospital_number
            if not patient_pool.check_nhs_number(cr, uid, data.get('patient_identifier'), context=context):
                _logger.warn("Patient registered from an update call - data available:%s" % data)
                self.register(cr, uid, hospital_number, data, context=context)
            else:
                patient_pool.update(cr, uid, data.get('patient_identifier'), nhs_data, selection='patient_identifier',
                                    context=context)
        if hospital_number:
            data.update({'other_identifier': hospital_number})
        update_activity = update_pool.create_activity(cr, uid, {}, {}, context=context)
        res = activity_pool.submit(cr, uid, update_activity, data, context=context)
        activity_pool.complete(cr, uid, update_activity, context=context)
        _logger.debug("Patient updated\n data: %s" % data)
        return res

    def register(self, cr, uid, hospital_number, data, context=None):
        """
        Registers a new patient into the system
        :param hospital_number: Hospital Number of the patient
        :param data: dictionary parameter that may contain the following keys:
            patient_identifier: NHS number
            family_name: Surname
            given_name: Name
            middle_names: Middle names
            dob: Date of birth
            gender: Gender (M/F)
            sex: Sex (M/F)
        """
        activity_pool = self.pool['nh.activity']
        register_pool = self.pool['nh.clinical.adt.patient.register']
        register_activity = register_pool.create_activity(cr, uid, {}, {}, context=context)
        if hospital_number:
            data.update({'other_identifier': hospital_number})
        activity_pool.submit(cr, uid, register_activity, data, context=context)
        res = activity_pool.complete(cr, uid, register_activity, context=context)
        _logger.debug("Patient registered\n data: %s" % data)
        return res

    def admit(self, cr, uid, hospital_number, data, context=None):
        """
        Admits a patient into the specified location.
        :param hospital_number: Hospital number of the patient
        :param data: dictionary parameter that may contain the following keys:
            location: location code where the patient will be admitted. REQUIRED
            start_date: admission start date.
            doctors: consulting and referring doctors list of dictionaries. expected format:
               [...
               {
               'type': 'c' or 'r',
               'code': code string,
               'title':, 'given_name':, 'family_name':, }
               ...]
                if doctor doesn't exist, we create partner, but don't create user for that doctor.
        """
        activity_pool = self.pool['nh.activity']
        patient_pool = self.pool['nh.clinical.patient']
        admit_pool = self.pool['nh.clinical.adt.patient.admit']
        if not patient_pool.check_hospital_number(cr, uid, hospital_number, context=context):
            nhs_data = data.copy()
            nhs_data['other_identifier'] = hospital_number
            if patient_pool.check_nhs_number(cr, uid, data.get('patient_identifier'), context=context):
                patient_pool.update(cr, uid, data.get('patient_identifier'), nhs_data, selection='patient_identifier',
                                    context=context)
            else:
                self.register(cr, uid, hospital_number, data, context=context)
        if hospital_number:
            data.update({'other_identifier': hospital_number})
        admit_activity = admit_pool.create_activity(cr, uid, {}, {}, context=context)
        activity_pool.submit(cr, uid, admit_activity, data, context=context)
        activity_pool.complete(cr, uid, admit_activity, context=context)
        _logger.debug("Patient admitted\n data: %s" % data)
        return True

    def admit_update(self, cr, uid, hospital_number, data, context=None):
        """
        Updates the spell information of the patient. Accepts the same parameters as admit.
        """
        activity_pool = self.pool['nh.activity']
        update_pool = self.pool['nh.clinical.adt.spell.update']
        patient_pool = self.pool['nh.clinical.patient']
        if not patient_pool.check_hospital_number(cr, uid, hospital_number, context=context):
            nhs_data = data.copy()
            nhs_data['other_identifier'] = hospital_number
            if patient_pool.check_nhs_number(cr, uid, data.get('patient_identifier'), context=context):
                patient_pool.update(cr, uid, data.get('patient_identifier'), nhs_data, selection='patient_identifier',
                                    context=context)
        if hospital_number:
            data.update({'other_identifier': hospital_number})
        update_activity = update_pool.create_activity(cr, uid, {}, {}, context=context)
        activity_pool.submit(cr, uid, update_activity, data, context=context)
        activity_pool.complete(cr, uid, update_activity, context=context)
        _logger.debug("Admission updated\n data: %s" % data)
        return True

    def cancel_admit(self, cr, uid, hospital_number, context=None):
        """
        Cancels the open admission of the patient.
        """
        activity_pool = self.pool['nh.activity']
        cancel_pool = self.pool['nh.clinical.adt.patient.cancel_admit']
        patient_pool = self.pool['nh.clinical.patient']
        patient_pool.check_hospital_number(cr, uid, hospital_number, exception='False', context=context)
        data = {'other_identifier': hospital_number}
        cancel_activity = cancel_pool.create_activity(cr, uid, {}, {}, context=context)
        activity_pool.submit(cr, uid, cancel_activity, data, context=context)
        activity_pool.complete(cr, uid, cancel_activity, context=context)
        _logger.debug("Admission cancelled\n data: %s" % data)
        return True

    def discharge(self, cr, uid, hospital_number, data, context=None):
        """
        Discharges the patient.
        :param hospital_number: Hospital number of the patient
        :param data: dictionary parameter that may contain the following keys:
            discharge_date: patient discharge date.
        """
        activity_pool = self.pool['nh.activity']
        discharge_pool = self.pool['nh.clinical.adt.patient.discharge']
        patient_pool = self.pool['nh.clinical.patient']
        if not patient_pool.check_hospital_number(cr, uid, hospital_number, context=context):
            nhs_data = data.copy()
            nhs_data['other_identifier'] = hospital_number
            if patient_pool.check_nhs_number(cr, uid, data.get('patient_identifier'), context=context):
                patient_pool.update(cr, uid, data.get('patient_identifier'), nhs_data, selection='patient_identifier',
                                    context=context)
        patientdb_id = patient_pool.search(cr, uid, [('other_identifier', '=', hospital_number)], context=context)
        spell_id = activity_pool.search(cr, uid, [['patient_id', '=', patientdb_id[0]],
                                                  ['state', 'not in', ['completed', 'cancelled']],
                                                  ['data_model', '=', 'nh.clinical.spell']], context=context)
        if not spell_id:
            raise osv.except_osv('Discharge Error!', 'Patient does not have an open spell!')
        discharge_activity = discharge_pool.create_activity(cr, uid,{
            'parent_id': spell_id[0],
            'patient_id': patientdb_id[0]}, {
            'other_identifier': hospital_number,
            'discharge_date': data.get('discharge_date')}, context=context)
        activity_pool.complete(cr, uid, discharge_activity, context=context)
        _logger.debug("Patient discharged: %s" % hospital_number)
        return True

    def cancel_discharge(self, cr, uid, hospital_number, context=None):
        """
        Cancels the last discharge of the patient.
        """
        patient_pool = self.pool['nh.clinical.patient']
        patient_pool.check_hospital_number(cr, uid, hospital_number, exception='False', context=context)
        activity_pool = self.pool['nh.activity']
        patient_pool = self.pool['nh.clinical.patient']
        cancel_pool = self.pool['nh.clinical.adt.patient.cancel_discharge']
        patientdb_id = patient_pool.search(cr, uid, [('other_identifier', '=', hospital_number)], context=context)
        cancel_discharge_activity = cancel_pool.create_activity(cr, uid, {'patient_id': patientdb_id[0]}, {}, context=context)
        activity_pool.submit(cr, uid, cancel_discharge_activity, {'other_identifier': hospital_number}, context=context)
        activity_pool.complete(cr, uid, cancel_discharge_activity, context=context)
        _logger.debug("Discharge cancelled for patient: %s" % hospital_number)
        return True

    def merge(self, cr, uid, hospital_number, data, context=None):
        """
        Merges a specified patient into the patient.
        :param hospital_number: Hospital number of the patient we want to merge INTO
        :param data: dictionary parameter that may contain the following keys:
            from_identifier: Hospital number of the patient we want to merge FROM
        """
        patient_pool = self.pool['nh.clinical.patient']
        patient_pool.check_hospital_number(cr, uid, hospital_number, exception='False', context=context)
        activity_pool = self.pool['nh.activity']
        merge_pool = self.pool['nh.clinical.adt.patient.merge']
        data.update({'into_identifier': hospital_number})
        merge_activity = merge_pool.create_activity(cr, uid, {}, {}, context=context)
        activity_pool.submit(cr, uid, merge_activity, data, context=context)
        activity_pool.complete(cr, uid, merge_activity, context=context)
        _logger.debug("Patient merged\n data: %s" % data)
        return True

    def transfer(self, cr, uid, hospital_number, data, context=None):
        """
        Transfers the patient to the specified location.
        :param hospital_number: Hospital number of the patient
        :param data: dictionary parameter that may contain the following keys:
            location: location code where the patient will be transferred. REQUIRED
        """
        activity_pool = self.pool['nh.activity']
        patient_pool = self.pool['nh.clinical.patient']
        transfer_pool = self.pool['nh.clinical.adt.patient.transfer']
        if not patient_pool.check_hospital_number(cr, uid, hospital_number, context=context):
            nhs_data = data.copy()
            nhs_data['other_identifier'] = hospital_number
            if patient_pool.check_nhs_number(cr, uid, data.get('patient_identifier'), context=context):
                patient_pool.update(cr, uid, data.get('patient_identifier'), nhs_data, selection='patient_identifier',
                                    context=context)
            else:
                self.register(cr, uid, hospital_number, data, context=context)
        patientdb_id = patient_pool.search(cr, uid, [('other_identifier', '=', hospital_number)], context=context)
        if hospital_number:
            data.update({'other_identifier': hospital_number})
        transfer_activity = transfer_pool.create_activity(cr, uid, {'patient_id': patientdb_id[0]}, {}, context=context)
        activity_pool.submit(cr, uid, transfer_activity, data, context=context)
        activity_pool.complete(cr, uid, transfer_activity, context=context)
        _logger.debug("Patient transferred\n data: %s" % data)
        return True

    def cancel_transfer(self, cr, uid, hospital_number, context=None):
        """
        Cancels the last transfer of the patient.
        """
        patient_pool = self.pool['nh.clinical.patient']
        patient_pool.check_hospital_number(cr, uid, hospital_number, exception='False', context=context)
        activity_pool = self.pool['nh.activity']
        cancel_pool = self.pool['nh.clinical.adt.patient.cancel_transfer']
        patientdb_id = patient_pool.search(cr, uid, [('other_identifier', '=', hospital_number)], context=context)
        cancel_transfer_activity = cancel_pool.create_activity(cr, uid, {'patient_id': patientdb_id[0]}, {}, context=context)
        activity_pool.submit(cr, uid, cancel_transfer_activity, {'other_identifier': hospital_number}, context=context)
        activity_pool.complete(cr, uid, cancel_transfer_activity, context=context)
        _logger.debug("Transfer cancelled for patient: %s" % hospital_number)
        return True