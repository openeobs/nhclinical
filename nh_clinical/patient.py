# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import logging

import re
from dateutil.parser import parse
from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

_logger = logging.getLogger(__name__)


class nh_clinical_patient(osv.Model):
    """
    Represents a patient.
    """
    _name = 'nh.clinical.patient'
    _description = "A Patient"

    _inherits = {'res.partner': 'partner_id'}

    _gender = [['BOTH', 'Both'], ['F', 'Female'], ['I', 'Intermediate'],
               ['M', 'Male'], ['NSP', 'Not Specified'], ['U', 'Unknown']]
    _ethnicity = [
        ['A', 'White - British'], ['B', 'White - Irish'],
        ['C', 'White - Other background'],
        ['D', 'Mixed - White and Black Caribbean'],
        ['E', 'Mixed - White and Black African'],
        ['F', 'Mixed - White and Asian'], ['G', 'Mixed - Other background'],
        ['H', 'Asian - Indian'], ['J', 'Asian - Pakistani'],
        ['K', 'Asian - Bangladeshi'], ['L', 'Asian - Other background'],
        ['M', 'Black - Caribbean'], ['N', 'Black - African'],
        ['P', 'Black - Other background'], ['R', 'Chinese'],
        ['S', 'Other ethnic group'], ['Z', 'Not stated']
    ]

    def _get_fullname(self, vals, fmt='{fn}, {gn} {mn}'):
        """
        Formats a fullname string from family, given and middle names.

        :param vals: contains 'family_name', 'given_name' and
            'middle_names'
        :type vals: dict
        :param fmt: format for fullname. Default is
                    '{fn}, {gn}, {mn}'
        :type fmt: string
        :returns: fullname
        :rtype: string
        """

        # for k in ['family_name', 'given_name', 'middle_names']:
        #     if k not in vals or vals[k] in [None, False]:
        #         vals.update({k: ''})
        for k in ['family_name', 'given_name']:
            if k not in vals or vals[k] in [None, False]:
                raise osv.except_osv(
                    'Integrity Error!',
                    'Patient must have a full name!')
        middle_names = vals.get('middle_names')
        if not middle_names:
            middle_names = ''

        return ' '.join(fmt.format(fn=vals.get('family_name'),
                                   gn=vals.get('given_name'),
                                   mn=middle_names).split())

    def _get_name(self, cr, uid, ids, fn, args, context=None):
        """
        Used by function field ``full_name`` to fetch the fullname for
        each patient given by patient id.

        :param ids: patient ids
        :type ids: list
        :returns: fullnames of patients
        :rtype: dict
        """

        result = dict.fromkeys(ids, False)
        for r in self.read(cr, uid, ids,
                           ['family_name', 'given_name', 'middle_names'],
                           context=context):
            # TODO This needs to be manipulable depending on locale
            result[r['id']] = self._get_fullname(r)
        return result

    def name_get(self, cr, uid, ids, context=None):
        """
        Override name_get method so we return the patient's fullname
        instead of the default name field
        """
        if not ids:
            return [(0, '')]
        if isinstance(ids, list):
            ids = ids[0]
        names = self.read(cr, uid, ids, [
            'family_name',
            'given_name',
            'middle_names'
        ], context=context)
        return [(ids, self._get_fullname(names))]

    def check_hospital_number(self, cr, uid, hospital_number, exception=False,
                              context=None):
        """
        Checks for a patient by `hospital number`.

        :param hospital_number: patient's hospital number
        :type hospital_number: string
        :param exception: ``True`` or ``False``. Default is ``False``
        :type exception: bool
        :returns: ``True`` if patient exists. Otherwise ``False``
        :rtype: bool
        :raises: :class:`except_orm<openerp.osv.osv.except_orm>` if
            ``exception`` is ``True`` and  if the patient exists or if
            the patient does not
        """
        if not hospital_number:
            result = False
        else:
            domain = [['other_identifier', '=', hospital_number]]
            result = bool(self.search(cr, uid, domain, context=context))
        if exception:
            if result and eval(exception):
                raise osv.except_osv(
                    'Integrity Error!',
                    'Patient with Hospital Number %s already exists!'
                    % hospital_number)
            elif not result and not eval(exception):
                raise osv.except_osv(
                    'Patient Not Found!',
                    'There is no patient with Hospital Number %s'
                    % hospital_number)
        return result

    def check_nhs_number(self, cr, uid, nhs_number, exception=False,
                         context=None):
        """
        Checks for patient by provided `NHS Number`.

        :param nhs_number: patient's nhs number
        :type nhs_number: string
        :param exception: ``True`` or ``False``. Default is ``False``
        :type exception: bool
        :returns: ``True`` if patient exists. Otherwise ``False``
        :rtype: bool
        :raises: :class:`except_orm<openerp.osv.osv.except_orm>` if
            ``exception`` is ``True`` and  if the patient exists or if
            the patient does not
        """

        if not nhs_number:
            result = False
        else:
            domain = [['patient_identifier', '=', nhs_number]]
            result = bool(self.search(cr, uid, domain, context=context))
        if exception:
            if result and eval(exception):
                raise osv.except_osv(
                    'Integrity Error!',
                    'Patient with NHS Number %s already exists!'
                    % nhs_number)
            elif not result and not eval(exception):
                raise osv.except_osv(
                    'Patient Not Found!',
                    'There is no patient with NHS Number %s'
                    % nhs_number)
        return result

    def update(self, cr, uid, identifier, data, selection='other_identifier',
               context=None):
        """
        Updates patient data by provided hospital number or nhs number,
        instead of patient_id as per usual.

        :param identifier: identifier of patient
        :type identifier: str
        :param data: data to write to the patient record
        :type data: dict
        :param selection: type of identifier used to lookup patient.
            Default is ``other_identifier``, which is `hospital number`.
            ``patient_identifier`` will do it through the nhs number.
        :type selection: str
        :returns: ``True``
        :rtype: bool
        """

        patient_id = self.search(cr, uid, [[selection, '=', identifier]],
                                 context=context)
        return self.write(cr, uid, patient_id, data, context=context)

    def _not_admitted(self, cr, uid, ids, fields, args, context=None):
        patient_ids_no_spell = self.get_not_admitted_patient_ids(
            cr, uid, context)
        result = {}
        for i in ids:
            result[i] = i in patient_ids_no_spell
        return result

    def _not_admitted_search(self, cr, uid, obj, name, args, domain=None,
                             context=None):
        """Function field method used by 'not_admitted' field."""
        patient_ids = []
        for condition in args:
            admitted_value = bool(condition[2])
            if condition[1] not in ['=', '!=']:
                continue

            all_patient_ids = self.search(cr, uid, [], context=context)
            patient_dict = self._not_admitted(
                cr, uid, all_patient_ids, 'not_admitted', None,
                context=context)

            if condition[1] == '=':
                patient_ids += [k for k, v in patient_dict.items()
                                if v == admitted_value]
            else:
                patient_ids += [k for k, v in patient_dict.items()
                                if v != admitted_value]

        return [('id', 'in', patient_ids)]

    _columns = {
        'current_location_id': fields.many2one('nh.clinical.location',
                                               'Current Location'),
        'partner_id': fields.many2one('res.partner', 'Partner', required=True,
                                      ondelete='cascade'),
        # res_partner birthdate is NOT a date
        'dob': fields.datetime('Date Of Birth'),
        'sex': fields.selection(_gender, 'Sex'),
        'gender': fields.selection(_gender, 'Gender'),
        'ethnicity': fields.selection(_ethnicity, 'Ethnicity'),
        'patient_identifier': fields.char('NHS Number', size=100,
                                          select=True, help="NHS Number"),
        'other_identifier': fields.char('Hospital Number', size=100,
                                        select=True, help="Hospital Number"),
        'given_name': fields.char('Given Name', size=200),
        'middle_names': fields.char('Middle Name(s)', size=200),
        'family_name': fields.char('Family Name', size=200, select=True),
        'full_name': fields.function(_get_name, type='text',
                                     string="Full Name"),
        'follower_ids': fields.many2many('res.users',
                                         'user_patient_rel',
                                         'patient_id',
                                         'user_id',
                                         'Followers'),
        'not_admitted': fields.function(_not_admitted, type='boolean',
                                        string='Not Admitted?',
                                        fnct_search=_not_admitted_search),
        'display_name':  fields.function(_get_name, type='text',
                                         string="Display Name")
    }

    _defaults = {
        'active': True,
        'name': 'unknown',
        'gender': 'NSP',
        'ethnicity': 'Z'
    }

    def load(self, cr, uid, fields, data, context=None):
        self.format_data(fields, data, context=context)
        return super(nh_clinical_patient, self).load(
            cr, uid, fields, data, context=context)

    def format_data(self, fields, data, context=None):
        if not context:
            context = dict()
        for index, field in enumerate(fields):
            if field == 'other_identifier' or field == 'patient_identifier':
                non_alphanumeric = re.compile(r'[\W_]+')
                for i, d in enumerate(data):
                    lst = list(d)
                    lst[index] = non_alphanumeric.sub('', lst[index])
                    data[i] = tuple(lst)
            if field == 'dob':
                if context.get('dateformat'):
                    yfirst = context['dateformat'] == 'YMD'
                    dfirst = context['dateformat'] == 'DMY'
                else:
                    yfirst = False
                    dfirst = False
                for i, d in enumerate(data):
                    lst = list(d)
                    lst[index] = parse(
                        lst[index], yearfirst=yfirst, dayfirst=dfirst
                    ).strftime(DTF)
                    data[i] = tuple(lst)

    def create(self, cr, uid, vals, context=None):
        """
        Extends Odoo's :meth:`create()<openerp.models.Model.create>`
        to write ``name``, ``other_identifier`` and
        ``patient_identifier`` upon creation.

        :returns: ``True`` if created
        :rtype: bool
        """
        if isinstance(vals, dict) and not vals.get('other_identifier') \
                and not vals.get('patient_identifier'):
            raise osv.except_osv(
                'Patient Data Error!',
                'Either the Hospital Number or the NHS Number is required '
                'to register/update a patient.')
        if not vals.get('name'):
            vals.update({'name': self._get_fullname(vals)})
        if vals.get('other_identifier'):
            self.check_hospital_number(cr, uid, vals.get('other_identifier'),
                                       exception='True', context=context)
        if vals.get('patient_identifier'):
            self.check_nhs_number(cr, uid, vals.get('patient_identifier'),
                                  exception='True', context=context)
        return super(nh_clinical_patient, self).create(
            cr, uid, vals,
            context=dict(context or {}, mail_create_nosubscribe=True))

    def write(self, cr, uid, ids, vals, context=None):
        """
        Extends Odoo's :meth:`write()<openerp.models.Model.write>`.

        :returns: ``True`` if created
        :rtype: bool
        """
        title_pool = self.pool['res.partner.title']
        keys = vals.keys()
        if 'title' in keys:
            if not isinstance(vals.get('title'), int):
                vals['title'] = title_pool.get_title_by_name(cr, uid,
                                                             vals['title'],
                                                             context=context)
        return super(nh_clinical_patient, self).write(cr, uid, ids, vals,
                                                      context=context)

    def unlink(self, cr, uid, ids, context=None):
        """
        "Deletes" a patient from the system without deleting the record
        from the database. This allows the retrieval of patient data
        if necessary.

        :param ids: ids of patients to unlink
        :type ids: list
        :returns: ``True``
        :rtype: bool
        """

        return super(nh_clinical_patient, self).write(cr, uid, ids,
                                                      {'active': False},
                                                      context=context)

    def check_data(self, cr, uid, data, create=True, exception=True,
                   context=None):
        """
        Default will check if patient exists. Either `hospital number`
        (``other_identifier``) or `NHS number` (``patient_identifier``)
        is required.

        If ``create`` is ``True``, then both ``other_identifier`` and
        ``patient_identifier`` must be unique. Otherwise either or both
        identifiers will be accepted in ``data`` parameter.

        If ``title`` is in ``data`` parameter, then method changes title
        to res.partner.title id. If ``title`` is not included, a new
        title will be created.

        :param data: must include either ``patient_identifier`` or
            ``other_identifier``
        :type data: dict
        :param create: ``True`` [default]
        :type create: bool
        :param exception: if ``True`` [default], it will raise an
            exception if no patient exists or more than one patient
            exists
        :type create: bool
        :raises: :class:`except_orm<openerp.osv.osv.except_orm>` if
            ``exception`` arguments is ``True`` and  if patient doesn't
            exists or if duplicate patients are found
        :returns: ``True`` if successful. Otherwise ``False``
        :rtype: bool
        """

        title_pool = self.pool['res.partner.title']
        if 'patient_identifier' not in data.keys() and \
                'other_identifier' not in data.keys():
            raise osv.except_osv(
                'Patient Data Error!',
                'Either the Hospital Number or the NHS Number is required to '
                'register/update a patient.')
        if create:
            if data.get('other_identifier'):
                self.check_hospital_number(cr, uid, data['other_identifier'],
                                           exception='True', context=context)
            if data.get('patient_identifier'):
                self.check_nhs_number(cr, uid, data['patient_identifier'],
                                      exception='True', context=context)
        else:
            if data.get('other_identifier') and data.get('patient_identifier'):
                domain = [
                    '|',
                    ['other_identifier', '=', data['other_identifier']],
                    ['patient_identifier', '=', data['patient_identifier']]
                ]
            elif data.get('other_identifier'):
                domain = [['other_identifier', '=', data['other_identifier']]]
            else:
                domain = [
                    ['patient_identifier', '=', data['patient_identifier']]
                ]
            patient_id = self.search(cr, uid, domain, context=context)
            if not patient_id:
                if exception:
                    raise osv.except_osv(
                        'Update Error!',
                        'No patient found with the provided identifier.')
                else:
                    return False
            if len(patient_id) > 1:
                if exception:
                    raise osv.except_osv(
                        'Update Error!',
                        'Identifiers for more than one patient provided.')
                else:
                    return False
            data['patient_id'] = patient_id[0]
        if 'title' in data.keys():
            if not isinstance(data.get('title'), int):
                data['title'] = title_pool.get_title_by_name(cr, uid,
                                                             data['title'],
                                                             context=context)
        return True

    def get_not_admitted_patient_ids(self, cr, uid, context=None):
        """Returns patients ids for patients with no open spell."""
        spell_pool = self.pool['nh.clinical.spell']
        spell_ids = spell_pool.search(
            cr, uid, [('state', '=', 'started')])
        spells = spell_pool.read(cr, uid, spell_ids, ['patient_id'])
        spell_patient_ids = set(spell['patient_id'][0] for spell in spells)
        all_patient_ids = set(self.search(cr, uid, []))
        all_patient_ids.difference_update(spell_patient_ids)
        return list(all_patient_ids)
