# -*- coding: utf-8 -*-
import logging

import re
from openerp import api
from openerp.osv import orm, fields

_logger = logging.getLogger(__name__)


class NhClinicalAdtPatientRegister(orm.Model):
    """
    Represents the patient register operation in the patient management
    system. (A28 Message)
    """
    _name = 'nh.clinical.adt.patient.register'
    _inherit = ['nh.activity.data']
    _description = 'ADT Patient Register'

    _gender = [
        ['BOTH', 'Both'],
        ['F', 'Female'],
        ['I', 'Intermediate'],
        ['M', 'Male'],
        ['NSP', 'Not Specified'],
        ['U', 'Unknown']
    ]
    _ethnicity = [
        ['A', 'White - British'],
        ['B', 'White - Irish'],
        ['C', 'White - Other background'],
        ['D', 'Mixed - White and Black Caribbean'],
        ['E', 'Mixed - White and Black African'],
        ['F', 'Mixed - White and Asian'],
        ['G', 'Mixed - Other background'],
        ['H', 'Asian - Indian'],
        ['J', 'Asian - Pakistani'],
        ['K', 'Asian - Bangladeshi'],
        ['L', 'Asian - Other background'],
        ['M', 'Black - Caribbean'],
        ['N', 'Black - African'],
        ['P', 'Black - Other background'],
        ['R', 'Chinese'],
        ['S', 'Other ethnic group'],
        ['Z', 'Not stated']
    ]

    _columns = {
        # Patient ID is not a required field because currently the patient is
        # created upon completion of the registration activity.
        # It's up for debate whether this should be refactored or is by design.
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient'),
        'patient_identifier': fields.char('NHS Number', size=10),
        'other_identifier': fields.char('Hospital Number', size=50,
                                        required=True),
        'family_name': fields.char('Last Name', size=200, required=True),
        'given_name': fields.char('First Name', size=200, required=True),
        'middle_names': fields.char('Middle Names', size=200),
        'dob': fields.datetime('Date of Birth'),
        'gender': fields.selection(_gender, string='Gender'),
        'sex': fields.selection(_gender, string='Sex'),
        'ethnicity': fields.selection(_ethnicity, string='Ethnicity'),
        'title': fields.many2one('res.partner.title', 'Title')
    }

    # There should only ever be one register record per patient.
    _sql_constraints = [
        (
            'patient_id_uniq',
            'unique(patient_id)',
            'A registration already exists for this patient.'
        ),
        (
            'patient_identifier_uniq',
            'unique(patient_identifier)',
            'Patient with this NHS Number already exists.'
        ),
        (
            'other_identifier_uniq',
            'unique(other_identifier)',
            'Patient with this Hospital Number already exists.'
        )
    ]

    def name_get(self, cr, uid, ids, context=None):
        """
        Get the referenced patients full name.
        """
        if not ids:
            return [(0, '')]
        if isinstance(ids, list):
            ids = ids[0]

        patient_pool = self.pool['nh.clinical.patient']
        names = self.read(cr, uid, ids, [
            'family_name',
            'given_name',
            'middle_names'
        ], context=context)
        return [(ids, patient_pool._get_fullname(names))]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        patient_model = self.env['nh.clinical.patient']
        args = args or []
        # Modify args as search will be done directly on patient model.
        for arg in args:  # args looks like [('a_field', '=', 'a_value')]
            field = arg[0]
            match = re.match(r"patient_id\.(.*)", field)
            if match:
                patient_field = match.group(1)
                arg[0] = patient_field

        patient_names = patient_model.name_search(
            name=name, args=args, operator=operator, limit=limit)
        patient_ids = map(lambda patient: patient[0], patient_names)
        registrations = self.search([('patient_id', 'in', patient_ids)])
        register_names = registrations.name_get()
        return register_names

    def create(self, cr, uid, vals, context):
        # Name field is not needed but is inherited from `nh.activity.data`.
        # When creating via the field in 'Create Patient Visit' Odoo adds this
        # key into the context which is used in `openerp.models.create()` to
        # actually populate the record. We don't want any value in this field.
        if context and 'default_name' in context:
            context = context.copy()
            del context['default_name']

        patient_pool = self.pool['nh.clinical.patient']
        patient_pool._validate_name(vals)
        patient_pool._validate_identifiers(vals)

        register_id = super(NhClinicalAdtPatientRegister, self).create(
            cr, uid, vals, context=context)
        return register_id

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

        patient = activity.data_ref.patient_id
        # If patient is not already created.
        if not patient:
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
        else:
            patient_id = patient.id

        activity_pool.write(
            cr, uid, activity_id,
            {'patient_id': patient_id}, context=context
        )
        self.write(
            cr, uid, activity.data_ref.id,
            {'patient_id': patient_id}, context=context
        )

        super(NhClinicalAdtPatientRegister, self).complete(
            cr, uid, activity_id, context)
        return patient_id
