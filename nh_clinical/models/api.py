# -*- coding: utf-8 -*-
# Part of NHClinical. See LICENSE file for full copyright and licensing details
"""
``api.py`` defines the core methods to interface with the
:mod:`adt` module.
"""
import logging

from openerp.osv import orm
from openerp.osv.osv import except_osv, except_orm

_logger = logging.getLogger(__name__)


class nh_clinical_api(orm.AbstractModel):
    """Core API for nh_clinical"""

    _name = 'nh.clinical.api'

    def _ensure_patient_is_registered(self, cr, uid, data, context=None):
        """
        If the patient does not already exist, register them.

        :param cr: Odoo Cursor
        :param uid: User's ID
        :param data: dict of data to update/register patient with
        :param context: Odoo context
        """
        hospital_number = data.get('other_identifier')
        nhs_number = data.get('patient_identifier')
        if not hospital_number and not nhs_number:
            raise except_osv(
                'Identifiers not provided',
                'Patient\'s NHS or Hospital numbers must be provided'
            )

        patient = None

        try:
            patient_pool = self.pool['nh.clinical.patient']
            patient = patient_pool.get_patient_for_identifiers(
                cr, uid,
                hospital_number=hospital_number,
                nhs_number=nhs_number,
                context=context)

            adt_register_pool = self.pool['nh.clinical.adt.patient.register']
            register_search_results = adt_register_pool.search(
                cr, uid, [('patient_id', '=', patient.id)])

            if register_search_results:
                registration_id = register_search_results[0]
                return registration_id

            # If execution reaches here then a patient was found for the passed
            # hospital number (as now exception was thrown) but there is no
            # register record found either. This shouldn't happen.
            _logger.warn('Found an existing patient that was not registered.')

        except except_orm:
            pass  # Fine if no patient found, we create them via registration.

        # If patient is already created then add values to be submitted for
        # ADT register record.
        if patient:
            data['patient_id'] = patient.id
            data['patient_identifier'] = patient.patient_identifier
            data['family_name'] = patient.family_name
            data['given_name'] = patient.given_name
            data['middle_names'] = patient.middle_names
            data['dob'] = patient.dob
            data['gender'] = patient.gender
            data['sex'] = patient.sex
            data['ethnicity'] = patient.ethnicity

        registration_id = self.register(
            cr, uid, hospital_number, data, context=context)
        return registration_id

    def verify_patient_exists(self, cr, uid, hospital_number, context=None):
        """
        Verify there's a patient in the system with the supplied hospital
        number

        :param cr: Odoo cursor
        :param uid: User ID
        :param hospital_number: Hospital number for patient
        :param context: odoo context
        """
        patient_pool = self.pool['nh.clinical.patient']
        patient_pool.get_patient_for_identifiers(
            cr, uid,
            hospital_number=hospital_number,
            context=context
        )

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

        update_pool = self.pool['nh.clinical.adt.patient.update']
        if hospital_number:
            data.update({'other_identifier': hospital_number})
        self._ensure_patient_is_registered(cr, uid, data, context=context)
        update_activity = update_pool.create_activity(
            cr, uid, {}, {}, context=context)
        res = activity_pool.submit(
            cr, uid, update_activity, data, context=context)
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
        adt_register_pool = self.pool['nh.clinical.adt.patient.register']
        if hospital_number:
            data.update({'other_identifier': hospital_number})

        register_id = adt_register_pool.create(cr, uid, {}, context=context)
        register = adt_register_pool.browse(
            cr, uid, register_id, context=context)
        activity_pool.submit(
            cr, uid, register.activity_id, data, context=context)
        activity_pool.complete(
            cr, uid, register.activity_id, context=context)

        register_activity = activity_pool.browse(cr, uid, register.activity_id)
        register = register_activity.data_ref

        _logger.debug("Patient registered\n data: %s", data)
        return register.id

    def admit(self, cr, uid, hospital_number, data, context=None):
        """
        Admits a patient into a specified location. Will register a new patient
        if one does not exist.

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
        adt_admit_pool = self.pool['nh.clinical.adt.patient.admit']

        if hospital_number:
            data.update({'other_identifier': hospital_number})

        registration_id = self._ensure_patient_is_registered(
            cr, uid, data, context=context)
        data['registration'] = registration_id

        admit_activity_id = adt_admit_pool.create_activity(
            cr, uid, {}, {}, context=context)
        activity_pool.submit(cr, uid, admit_activity_id, data, context=context)
        activity_pool.complete(cr, uid, admit_activity_id, context=context)

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
        if hospital_number:
            data.update({'other_identifier': hospital_number})
        self._ensure_patient_is_registered(cr, uid, data, context=context)
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
        self.verify_patient_exists(cr, uid, hospital_number, context=context)
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
        if hospital_number:
            data.update({'other_identifier': hospital_number})
        self._ensure_patient_is_registered(cr, uid, data, context=context)
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

        self.verify_patient_exists(cr, uid, hospital_number, context=context)
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

        self.verify_patient_exists(cr, uid, hospital_number, context=context)
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
        transfer_pool = self.pool['nh.clinical.adt.patient.transfer']
        if hospital_number:
            data.update({'other_identifier': hospital_number})
        self._ensure_patient_is_registered(cr, uid, data, context=context)
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

        self.verify_patient_exists(cr, uid, hospital_number, context=context)
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
        domain = [
            ('id', '=', activity_id),
            '|',
            ('user_ids', 'in', [uid]),
            ('user_id', '=', uid)
        ]
        activity_ids = activity_pool.search(cr, uid, domain, context=context)
        if not activity_ids:
            return False
        user_id = activity_pool.read(
            cr, uid, activity_id, ['user_id'], context=context)['user_id']
        if user_id and user_id[0] != uid:
            return False
        return True
