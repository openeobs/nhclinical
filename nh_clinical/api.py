# -*- coding: utf-8 -*-
# Part of NHClinical. See LICENSE file for full copyright and licensing details
"""
``api.py`` defines the core methods to interface with the
:mod:`adt` module.
"""
import logging

from openerp.osv import orm


_logger = logging.getLogger(__name__)


class nh_clinical_api(orm.AbstractModel):
    """Core API for nh_clinical"""

    _name = 'nh.clinical.api'

    def update(self, cr, uid, hospital_number, data, context=None):
        """
        Update patient information.

        :param hospital_number: hospital number of the patient
        :type hospital_number: str
        :param data: may contain the following keys:
            ``patient_identifier`` and ``other_identifier`` among
            others
        :type data: dict
        :returns: ``True``
        :rtype: bool
        """

        activity_pool = self.pool['nh.activity']
        patient_pool = self.pool['nh.clinical.patient']
        update_pool = self.pool['nh.clinical.adt.patient.update']
        if not patient_pool.check_hospital_number(cr, uid, hospital_number,
                                                  context=context):
            nhs_data = data.copy()
            nhs_data['other_identifier'] = hospital_number
            if not patient_pool.check_nhs_number(
                    cr, uid, data.get('patient_identifier'), context=context):
                _logger.warn("Patient registered from an update call - "
                             "data available:%s", data)
                self.register(cr, uid, hospital_number, data, context=context)
            else:
                patient_pool.update(cr, uid, data.get('patient_identifier'),
                                    nhs_data, selection='patient_identifier',
                                    context=context)
        if hospital_number:
            data.update({'other_identifier': hospital_number})
        update_activity = update_pool.create_activity(cr, uid, {}, {},
                                                      context=context)
        res = activity_pool.submit(cr, uid, update_activity, data,
                                   context=context)
        activity_pool.complete(cr, uid, update_activity, context=context)
        _logger.debug("Patient updated\n data: %s", data)
        return res

    def register(self, cr, uid, hospital_number, data, context=None):
        """
        Registers a new patient in the system.

        :param hospital_number: hospital number of the patient
        :type hospital_number: str
        :param data: may contain the following keys:
            ``patient_identifier``, ``family_name``, ``given_name``,
            ``middle_names``, ``dob``, ``gender`` and ``sex``
        :returns: ``True``
        :rtype: bool
        """

        activity_pool = self.pool['nh.activity']
        register_pool = self.pool['nh.clinical.adt.patient.register']
        register_activity = register_pool.create_activity(cr, uid, {}, {},
                                                          context=context)
        if hospital_number:
            data.update({'other_identifier': hospital_number})
        activity_pool.submit(cr, uid, register_activity, data, context=context)
        res = activity_pool.complete(cr, uid, register_activity,
                                     context=context)
        _logger.debug("Patient registered\n data: %s", data)
        return res

    def admit(self, cr, uid, hospital_number, data, context=None):
        """
        Admits a patient into a specified location.

        :param hospital_number: Hospital number of the patient
        :type hospital_number: str
        :param data: contains ``location_code``, ``start_date`` and a
            list of dictionaries of consulting and referring doctors,
            containing the following keys: ``type``, ``code``,
            ``title``, ``given_name`` and ``family_name``
        :type data: dict
        :returns: ``True``
        :rtype: bool
        """

        activity_pool = self.pool['nh.activity']
        patient_pool = self.pool['nh.clinical.patient']
        admit_pool = self.pool['nh.clinical.adt.patient.admit']
        if not patient_pool.check_hospital_number(cr, uid, hospital_number,
                                                  context=context):
            nhs_data = data.copy()
            nhs_data['other_identifier'] = hospital_number
            if patient_pool.check_nhs_number(
                    cr, uid, data.get('patient_identifier'), context=context):
                patient_pool.update(cr, uid, data.get('patient_identifier'),
                                    nhs_data, selection='patient_identifier',
                                    context=context)
            else:
                self.register(cr, uid, hospital_number, data, context=context)
        if hospital_number:
            data.update({'other_identifier': hospital_number})
        admit_activity = admit_pool.create_activity(cr, uid, {}, {},
                                                    context=context)
        activity_pool.submit(cr, uid, admit_activity, data, context=context)
        activity_pool.complete(cr, uid, admit_activity, context=context)
        _logger.debug("Patient admitted\n data: %s", data)
        return True

    def admit_update(self, cr, uid, hospital_number, data, context=None):
        """
        Updates the spell information of a patient.

        :param hospital_number: hospital number of the patient
        :type hospital_number: str
        :param data: may contain ``other_identifier`` and
            ``patient_identifier`` among others
        :type data: dict
        :returns: ``True``
        :rtype: bool
        """

        activity_pool = self.pool['nh.activity']
        update_pool = self.pool['nh.clinical.adt.spell.update']
        patient_pool = self.pool['nh.clinical.patient']
        if not patient_pool.check_hospital_number(cr, uid, hospital_number,
                                                  context=context):
            nhs_data = data.copy()
            nhs_data['other_identifier'] = hospital_number
            if patient_pool.check_nhs_number(
                    cr, uid, data.get('patient_identifier'), context=context):
                patient_pool.update(cr, uid, data.get('patient_identifier'),
                                    nhs_data, selection='patient_identifier',
                                    context=context)
            else:
                self.register(cr, uid, hospital_number, data, context=context)
        if hospital_number:
            data.update({'other_identifier': hospital_number})
        update_activity = update_pool.create_activity(cr, uid, {}, {},
                                                      context=context)
        activity_pool.submit(cr, uid, update_activity, data, context=context)
        activity_pool.complete(cr, uid, update_activity, context=context)
        _logger.debug("Admission updated\n data: %s", data)
        return True

    def cancel_admit(self, cr, uid, hospital_number, context=None):
        """
        Cancels the open admission of the patient.

        :param hospital_number: hospital number of the patient
        :type hospital_number: str
        :returns: ``True``
        :rtype: bool
        """

        activity_pool = self.pool['nh.activity']
        cancel_pool = self.pool['nh.clinical.adt.patient.cancel_admit']
        patient_pool = self.pool['nh.clinical.patient']
        patient_pool.check_hospital_number(cr, uid, hospital_number,
                                           exception='False', context=context)
        data = {'other_identifier': hospital_number}
        cancel_activity = cancel_pool.create_activity(cr, uid, {}, {},
                                                      context=context)
        activity_pool.submit(cr, uid, cancel_activity, data, context=context)
        activity_pool.complete(cr, uid, cancel_activity, context=context)
        _logger.debug("Admission cancelled\n data: %s", data)
        return True

    def discharge(self, cr, uid, hospital_number, data, context=None):
        """
        Discharges a patient.

        :param hospital_number: hospital number of the patient
        :type hospital_number: str
        :param data: may contain the key ``discharge_date``
        :type data: dict
        :returns: ``True``
        :rtype: bool
        """

        activity_pool = self.pool['nh.activity']
        discharge_pool = self.pool['nh.clinical.adt.patient.discharge']
        patient_pool = self.pool['nh.clinical.patient']
        if not patient_pool.check_hospital_number(cr, uid, hospital_number,
                                                  context=context):
            nhs_data = data.copy()
            nhs_data['other_identifier'] = hospital_number
            if patient_pool.check_nhs_number(
                    cr, uid, data.get('patient_identifier'), context=context):
                patient_pool.update(cr, uid, data.get('patient_identifier'),
                                    nhs_data, selection='patient_identifier',
                                    context=context)
            else:
                self.register(cr, uid, hospital_number, data, context=context)
        if hospital_number:
            data.update({'other_identifier': hospital_number})
        discharge_activity = discharge_pool.create_activity(cr, uid, {}, {},
                                                            context=context)
        activity_pool.submit(cr, uid, discharge_activity, data,
                             context=context)
        activity_pool.complete(cr, uid, discharge_activity, context=context)
        _logger.debug("Patient discharged: %s", hospital_number)
        return True

    def cancel_discharge(self, cr, uid, hospital_number, context=None):
        """
        Cancels the last discharge of a patient.

        :param hospital_number: hospital number of the patient
        :type hospital_number: str
        :returns: ``True``
        :rtype: bool
        """

        patient_pool = self.pool['nh.clinical.patient']
        patient_pool.check_hospital_number(cr, uid, hospital_number,
                                           exception='False', context=context)
        activity_pool = self.pool['nh.activity']
        cancel_pool = self.pool['nh.clinical.adt.patient.cancel_discharge']
        cancel_discharge_activity = cancel_pool.create_activity(
            cr, uid, {}, {}, context=context)
        activity_pool.submit(cr, uid, cancel_discharge_activity,
                             {'other_identifier': hospital_number},
                             context=context)
        activity_pool.complete(cr, uid, cancel_discharge_activity,
                               context=context)
        _logger.debug("Discharge cancelled for patient: %s", hospital_number)
        return True

    def merge(self, cr, uid, hospital_number, data, context=None):
        """
        Merges a specified patient into a patient.

        :param hospital_number: hospital number of the patient merged
            INTO
        :type hospital_number: str
        :param data: may contain the key ``from_identifier``,
            the hospital number of the patient merged FROM
        :type data: dict
        :returns: ``True``
        :rtype: bool
        """

        patient_pool = self.pool['nh.clinical.patient']
        patient_pool.check_hospital_number(cr, uid, hospital_number,
                                           exception='False', context=context)
        activity_pool = self.pool['nh.activity']
        merge_pool = self.pool['nh.clinical.adt.patient.merge']
        data.update({'into_identifier': hospital_number})
        merge_activity = merge_pool.create_activity(cr, uid, {}, {},
                                                    context=context)
        activity_pool.submit(cr, uid, merge_activity, data, context=context)
        activity_pool.complete(cr, uid, merge_activity, context=context)
        _logger.debug("Patient merged\n data: %s", data)
        return True

    def transfer(self, cr, uid, hospital_number, data, context=None):
        """
        Transfers the patient to a specified location.

        :param hospital_number: hospital number of the patient
        :type hospital_number: str
        :param data: required is ``location_code`` of the patient's
            transfer destination
        :type data: dict
        :returns: ``True``
        :rtype: bool
        """

        activity_pool = self.pool['nh.activity']
        patient_pool = self.pool['nh.clinical.patient']
        transfer_pool = self.pool['nh.clinical.adt.patient.transfer']
        if not patient_pool.check_hospital_number(cr, uid, hospital_number,
                                                  context=context):
            nhs_data = data.copy()
            nhs_data['other_identifier'] = hospital_number
            if patient_pool.check_nhs_number(
                    cr, uid, data.get('patient_identifier'), context=context):
                patient_pool.update(cr, uid, data.get('patient_identifier'),
                                    nhs_data, selection='patient_identifier',
                                    context=context)
            else:
                self.register(cr, uid, hospital_number, data, context=context)
        if hospital_number:
            data.update({'other_identifier': hospital_number})
        transfer_activity = transfer_pool.create_activity(cr, uid, {}, {},
                                                          context=context)
        activity_pool.submit(cr, uid, transfer_activity, data, context=context)
        activity_pool.complete(cr, uid, transfer_activity, context=context)
        _logger.debug("Patient transferred\n data: %s", data)
        return True

    def cancel_transfer(self, cr, uid, hospital_number, context=None):
        """
        Cancels the last transfer of a patient.

        :param hospital_number: hospital number of the patient
        :type hospital_number: str
        :returns: ``True``
        :rtype: bool
        """

        patient_pool = self.pool['nh.clinical.patient']
        patient_pool.check_hospital_number(cr, uid, hospital_number,
                                           exception='False', context=context)
        activity_pool = self.pool['nh.activity']
        cancel_pool = self.pool['nh.clinical.adt.patient.cancel_transfer']
        cancel_transfer_activity = cancel_pool.create_activity(
            cr, uid, {}, {}, context=context)
        activity_pool.submit(
            cr, uid, cancel_transfer_activity,
            {'other_identifier': hospital_number}, context=context)
        activity_pool.complete(cr, uid, cancel_transfer_activity,
                               context=context)
        _logger.debug("Transfer cancelled for patient: %s", hospital_number)
        return True

    def check_activity_access(self, cr, uid, activity_id, context=None):
        """
        Verifies if an :class:`activity<activity.nh_activity>` is
        assigned to a :class:`user<base.res_users>`.

        :param uid: id of user to verify
        :type uid: int
        :param activity_id: id of activity to verify
        :type activity_id: int
        :returns: ``True`` if user is assigned. Otherwise ``False``
        :rtype: bool
        """
        activity_pool = self.pool['nh.activity']
        domain = [('id', '=', activity_id), '|', ('user_ids', 'in', [uid]),
                  ('user_id', '=', uid)]
        activity_ids = activity_pool.search(cr, uid, domain, context=context)
        if not activity_ids:
            return False
        user_id = activity_pool.read(
            cr, uid, activity_id, ['user_id'], context=context)['user_id']
        if user_id and user_id[0] != uid:
            return False
        return True
