# -*- coding: utf-8 -*-
# Part of NHClinical. See LICENSE file for full copyright and licensing details
import logging
import re
from dateutil.parser import parse

from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from openerp import api
from openerp.exceptions import ValidationError
from openerp.addons.nh_odoo_fixes.validate import validate_non_empty_string

_logger = logging.getLogger(__name__)


class NhClinicalPatient(osv.Model):
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

    _sql_constraints = [
        (
            'patient_identifier',
            'unique(patient_identifier)',
            'Patient with this NHS Number already exists'
        ),
        (
            'other_identifier',
            'unique(other_identifier)',
            'Patient with this Hospital Number already exists'
        )
    ]

    @staticmethod
    def _check_identifier_for_bad_chars(value):
        """
        Check for bad characters in string

        :param value: string to check
        """
        allowed_chars = r'[a-zA-Z0-9_\-\s]'
        match = re.match(allowed_chars, value)
        if not match:
            raise ValidationError(
                'Patient identifier can only contain '
                'alphanumeric characters, hyphens and underscores'
            )

    @staticmethod
    def _remove_whitespace(value):
        """
        Remove white space from the supplied string, return None if would
        be empty string

        :param value: string to remove whitespace from
        :return: string without whitespace
        """
        spaces = r'\s'
        val = re.sub(spaces, '', value)
        return val if val else None

    def _clean_identifiers(self, dirty_vals):
        """
        Clean up the patient identifiers by removing non-alpha numerical
        characters

        :param dirty_vals: Dictionary of values which contains identifiers
            which need cleaning
        :return: Dictionary of values with squeaky clean identifiers
        """
        vals = dirty_vals.copy()
        hospital_number = vals.get('other_identifier')
        nhs_number = vals.get('patient_identifier')
        if hospital_number:
            self._check_identifier_for_bad_chars(hospital_number)
            vals['other_identifier'] = self._remove_whitespace(hospital_number)
        if nhs_number:
            self._check_identifier_for_bad_chars(nhs_number)
            vals['patient_identifier'] = self._remove_whitespace(nhs_number)
        return vals

    @staticmethod
    def _validate_indentifiers(vals):
        """
        Validate that the value dict has at least one of:
        - NHS Number
        - Hospital Number

        :param vals: dictionary of patient values
        :return: True
        """
        if not vals.get('other_identifier'):
            raise ValidationError(
                'Patient record must have Hospital number')
        return True

    @staticmethod
    def _validate_name(vals):
        """
        Validate that the value dict has both:
        - given_name
        - family_name

        :param vals: dictionary of patient values
        :return: True
        """
        if not vals.get('given_name') or not vals.get('family_name'):
            raise ValidationError(
                'Patient record must have valid Given and Family Names'
            )
        return True

    @api.constrains('patient_identifier', 'other_identifier')
    def _check_identifiers_defined(self):
        """
        Check that the record contains at least an NHS or Hospital number
        """
        vals_dict = {
            'patient_identifier':
                validate_non_empty_string(self.patient_identifier),
            'other_identifier':
                validate_non_empty_string(self.other_identifier)
        }
        self._validate_indentifiers(vals_dict)

    @api.constrains('given_name', 'family_name')
    def _check_patient_names(self):
        """
        Check that the patient's name is actually set as Odoo's required flag
        can be fooled by a string made of just spaces
        """
        vals = {
            'given_name': validate_non_empty_string(self.given_name),
            'family_name': validate_non_empty_string(self.family_name)
        }
        self._validate_name(vals)

    def _get_fullname(self, vals, fmt=None):
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
        if not fmt:
            fmt = '{family_name}, {given_name} {middle_names}'
        name = {
            k: vals.get(k) for k in (
                'family_name',
                'given_name',
                'middle_names'
            )
        }
        for key, value in name.items():
            if not validate_non_empty_string(value):
                name[key] = ''
        return ' '.join(fmt.format(**name).split())

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
        'other_identifier': fields.char(
            'Hospital Number', size=100, select=True,
            help="Hospital Number", required=True),
        'given_name': fields.char(
            'Given Name', size=200, required=True),
        'middle_names': fields.char('Middle Name(s)', size=200),
        'family_name': fields.char(
            'Family Name', size=200, select=True, required=True),
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
        return super(NhClinicalPatient, self).load(
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
        vals = self._clean_identifiers(vals)
        self._validate_indentifiers(vals)
        self._validate_name(vals)
        if not vals.get('name'):
            vals.update({'name': self._get_fullname(vals)})
        return super(NhClinicalPatient, self).create(
            cr, uid, vals,
            context=dict(context or {}, mail_create_nosubscribe=True))

    def write(self, cr, uid, ids, vals, context=None):
        """
        Extends Odoo's :meth:`write()<openerp.models.Model.write>`.

        :returns: ``True`` if created
        :rtype: bool
        """
        vals = self._clean_identifiers(vals)
        title_pool = self.pool['res.partner.title']
        keys = vals.keys()
        if 'title' in keys:
            if not isinstance(vals.get('title'), int):
                vals['title'] = title_pool.get_title_by_name(
                    cr, uid, vals['title'], context=context)
        return super(NhClinicalPatient, self).write(
            cr, uid, ids, vals, context=context)

    @api.model
    def get_patient_id_for_identifiers(
            self, hospital_number=None, nhs_number=None):
        """
        Get patient record with either of the supplied identifier or raise
        error

        :param hospital_number: Other identifier for the patient record
        :param nhs_number: Patient identifier for the patient record
        :return: patient ID for patient with either of the identifiers
        """
        if not hospital_number and not nhs_number:
            raise osv.except_osv(
                'Identifiers not provided',
                'Patient\'s NHS or Hospital numbers must be provided'
            )
        search_filter = []
        if hospital_number:
            search_filter.append(['other_identifier', '=', hospital_number])
        if nhs_number:
            search_filter.append(['patient_identifier', '=', nhs_number])
        if len(search_filter) > 1:
            search_filter.insert(0, '|')
        patient_id = self.search(search_filter)
        if not patient_id:
            raise osv.except_osv(
                'Patient Not Found!',
                'There is no patient in system with credentials provided')
        else:
            return patient_id[0]

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

        return super(NhClinicalPatient, self).write(
            cr, uid, ids, {'active': False}, context=context)

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

    @api.model
    def get_patients_on_ward(self, ward_id, patient_ids=None):
        domain = [('current_location_id', 'child_of', ward_id)]
        if isinstance(patient_ids, list):
            domain.append(('id', 'in', patient_ids))
        elif isinstance(patient_ids, int):
            domain.append(('id', '=', patient_ids))
        patients_on_ward = self.search(domain)
        return patients_on_ward

    @api.one
    def serialise(self):
        patient_dict = {
            'id': self.id,
            'full_name': self.full_name,
            # TODO See why this was substringed in the old SQL query.
            'patient_identifier': self.patient_identifier,
            'other_identifier': self.other_identifier,
            'dob': self.dob,
            'gender': self.gender,
            'sex': self.sex,
            'location': self.current_location_id.name,
            'parent_location': self.current_location_id.parent_id.name
        }
        return patient_dict
