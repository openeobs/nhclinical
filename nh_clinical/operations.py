# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
"""
``operations.py`` defines a set of activity types to deal with
hospital administrative tasks like patient movements, admissions,
discharge, etc.
"""
import logging

from openerp.osv import orm, fields, osv
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class nh_clinical_patient_move(orm.Model):
    """
    Represents any physical patient movement between different instances
    of :mod:`location<base.nh_clinical_location>`.

    It is meant to work as an audit mechanism to track any patient
    movements within the Hospital.
    """
    _name = 'nh.clinical.patient.move'
    _inherit = ['nh.activity.data']
    _description = "Patient Move"
    _start_view_xmlid = "view_patient_move_form"
    _schedule_view_xmlid = "view_patient_move_form"
    _submit_view_xmlid = "view_patient_move_form"
    _complete_view_xmlid = "view_patient_move_form"
    _cancel_view_xmlid = "view_patient_move_form"
    _columns = {
        'location_id': fields.many2one('nh.clinical.location',
                                       'Destination Location'),
        'location_name': fields.related(
            'location_id', 'full_name', type='char', size=150,
            string='Destination Location'),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient',
                                      required=True),
        'reason': fields.text('Reason'),
        'from_location_id': fields.many2one('nh.clinical.location',
                                            'Source Location')
    }

    _order = 'id desc'

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data and then calls
        :meth:`submit<activity.nh_activity.submit>`.

        :returns: ``True``
        :rtype: bool
        """
        data = vals.copy()
        if 'patient_id' in vals and 'parent_id' not in vals:
            spell_pool = self.pool['nh.clinical.spell']
            activity_pool = self.pool['nh.activity']
            spell_id = spell_pool.get_by_patient_id(
                cr, uid, vals['patient_id'], context=context)
            if spell_id:
                spell = spell_pool.browse(cr, uid, spell_id, context=context)
                activity_pool.write(
                    cr, uid, activity_id, {'parent_id': spell.activity_id.id},
                    context=context)
        return super(nh_clinical_patient_move, self).submit(
            cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Updates the patient ``current_location_id`` and the related
        :mod:`spell<spell.nh_clinical_spell>` ``location_id`` and then
        calls :meth:`complete<activity.nh_activity.complete>`.

        :returns: ``True``
        :rtype:  bool
        """
        activity_pool = self.pool['nh.activity']
        patient_pool = self.pool['nh.clinical.patient']
        activity = activity_pool.browse(cr, uid, activity_id, context)
        if not activity.location_id:
            raise osv.except_osv("Patient Move Error!",
                                 'There is no destination location!')

        last_movement_id = activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.patient.move'],
            ['state', '=', 'completed'],
            ['patient_id', '=', activity.patient_id.id]
        ], order='sequence desc', context=context)
        last_movement_id = last_movement_id[0] if last_movement_id else False
        last_movement = activity_pool.browse(
            cr, uid, last_movement_id, context=context
        ) if last_movement_id else False

        if last_movement:
            location_id = last_movement.data_ref.location_id.id
        else:
            location_id = False
        self.write(cr, uid, activity.data_ref.id,
                   {'from_location_id': location_id})
        patient_pool.write(
            cr, uid, activity.data_ref.patient_id.id,
            {'current_location_id': activity.data_ref.location_id.id},
            context=context)
        if activity.parent_id:
            activity_pool.submit(
                cr, uid, activity.parent_id.id,
                {'location_id': activity.data_ref.location_id.id},
                context=context)
        return super(nh_clinical_patient_move, self).complete(
            cr, uid, activity_id, context)


class nh_clinical_patient_swap_beds(orm.Model):
    """
    Represents the simultaneous movement of two patients that are
    located in `bed` usage :mod:`location<base.nh_clinical_location>`
    instances.
    The patients will end placed in the location the other patient was
    in.

    It is meant to be used to move patients specially when there are no
    available beds to use as a buffer, although it can be used any time.
    """
    _name = 'nh.clinical.patient.swap_beds'
    _inherit = ['nh.activity.data']
    _description = "Patient Swap"
    _columns = {
        'location1_id': fields.many2one(
            'nh.clinical.location',
            'Location 1', domain=[['usage', '=', 'bed']], required=True),
        'location2_id': fields.many2one(
            'nh.clinical.location', 'Location 2',
            domain=[['usage', '=', 'bed']], required=True),
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data is correct and then calls
        :meth:`submit<activity.nh_activity.submit>`.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_patient_swap_beds, self).submit(
            cr, uid, activity_id, vals, context=context)
        activity_pool = self.pool['nh.activity']
        location_pool = self.pool['nh.clinical.location']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        location1 = activity.data_ref.location1_id
        location2 = activity.data_ref.location2_id
        if location1 and not location1.patient_ids:
            raise osv.except_osv('Swap Patients Error!',
                                 'No patient in location %s' %
                                 location1.name)
        if location2 and not location2.patient_ids:
            raise osv.except_osv('Swap Patients Error!',
                                 'No patient in location %s' %
                                 location2.name)
        ward1_id = location_pool.get_closest_parent_id(cr, uid, location1.id,
                                                       'ward', context=context)
        ward2_id = location_pool.get_closest_parent_id(cr, uid, location2.id,
                                                       'ward', context=context)
        if ward1_id != ward2_id:
            raise osv.except_osv(
                'Swap Patients Error!',
                'Trying to swap locations from '
                'different wards, should be using transfer instead')
        return res

    def complete(self, cr, uid, activity_id, context=None):
        """
        Creates and completes a
        :mod:`movement<operations.nh_clinical_patient_move>` for each
        patient to swap their locations.

        :returns: ``True``
        :rtype: bool
        """
        activity_pool = self.pool['nh.activity']
        move_pool = self.pool['nh.clinical.patient.move']
        spell_pool = self.pool['nh.clinical.spell']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        location1 = activity.data_ref.location1_id
        location2 = activity.data_ref.location2_id
        patient1 = location1.patient_ids[0]
        patient2 = location2.patient_ids[0]
        spell1_id = spell_pool.get_by_patient_id(cr, uid, patient1.id,
                                                 context=context)
        spell2_id = spell_pool.get_by_patient_id(cr, uid, patient2.id,
                                                 context=context)
        spell1 = spell_pool.browse(cr, uid, spell1_id, context=context)
        spell2 = spell_pool.browse(cr, uid, spell2_id, context=context)

        move1_id = move_pool.create_activity(
            cr, uid,
            {'parent_id': spell1.activity_id.id, 'creator_id': activity_id},
            {'location_id': location2.id, 'patient_id': patient1.id},
            context=context)
        move2_id = move_pool.create_activity(
            cr, uid,
            {'parent_id': spell2.activity_id.id, 'creator_id': activity_id},
            {'location_id': location1.id, 'patient_id': patient2.id},
            context=context)
        activity_pool.complete(cr, uid, move1_id, context=context)
        activity_pool.complete(cr, uid, move2_id, context=context)
        return super(nh_clinical_patient_swap_beds, self).complete(
            cr, uid, activity_id, context=context)


class nh_clinical_patient_placement(orm.Model):
    """
    Represents the action of assigning a `bed` usage
    :mod:`location<base.nh_clinical_location>` to an admitted patient.
    """
    _name = 'nh.clinical.patient.placement'
    _inherit = ['nh.activity.data']
    _description = "Patient Placement"
    _start_view_xmlid = "view_patient_placement_form"
    _schedule_view_xmlid = "view_patient_placement_form"
    _submit_view_xmlid = "view_patient_placement_form"
    _complete_view_xmlid = "view_patient_placement_complete"
    _cancel_view_xmlid = "view_patient_placement_form"

    _columns = {
        'suggested_location_id': fields.many2one(
            'nh.clinical.location', 'Suggested Location', required=True),
        'location_id': fields.many2one('nh.clinical.location',
                                       'Destination Location'),
        'patient_id': fields.many2one('nh.clinical.patient',
                                      'Patient', required=True),
        'reason': fields.text('Reason'),
        'pos_id': fields.related('activity_id', 'pos_id', type='many2one',
                                 relation='nh.clinical.pos', string='POS'),
    }

    _form_description = [
        {
            'name': 'location_id',
            'type': 'selection',
            'label': 'Location',
            'initially_hidden': False
        }
    ]

    def get_form_description(self, cr, uid, patient_id, context=None):
        """
         Returns a description in dictionary format of the input fields
         that would be required in the user gui when completing this
         action.

        :param patient_id: :mod:`patient<base.nh_clinical_patient>` id
        :type patient_id: int
        :returns: a list of dictionaries
        :rtype: list
        """
        activity_pool = self.pool['nh.activity']
        location_pool = self.pool['nh.clinical.location']
        form_desc = list(self._form_description)
        # Find Available Beds
        placement_ids = activity_pool.search(cr, uid, [
            ('patient_id', '=', patient_id),
            ('state', 'not in', ['completed', 'cancelled']),
            ('data_model', '=', 'nh.clinical.patient.placement')
        ], order='id desc', context=context)
        location_selection = []
        if placement_ids:
            placement = activity_pool.browse(cr, uid, placement_ids[0],
                                             context=context)
            location_ids = location_pool.search(cr, uid, [
                ('usage', '=', 'bed'),
                ('parent_id', 'child_of', placement.location_id.id),
                ('is_available', '=', True)
            ], context=context)
            location_selection = [[l, location_pool.read(
                cr, uid, l, ['name'],
                context=context)['name']] for l in location_ids]
        for field in form_desc:
            if field['name'] == 'location_id':
                field['selection'] = location_selection
        return form_desc

    def get_activity_location_id(self, cr, uid, activity_id, context=None):
        """
        Returns the :mod:`location<base.nh_clinical_location>` where the
        patient is waiting to be placed, usually of `ward` usage.

        :returns: :mod:`location<base.nh_clinical_location>` id
        :rtype: int
        """
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context)
        return activity.data_ref.suggested_location_id.id

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        creates and completes a
        :mod:`movement<operations.nh_clinical_patient_move>` to the
        selected `bed` usage location.

        This operation will kick off a policy trigger as Hospitals
        usually start observations or measurements on patients after
        this action is taken.

        :returns: ``True``
        :rtype: bool
        """
        activity_pool = self.pool['nh.activity']
        spell_pool = self.pool['nh.clinical.spell']
        move_pool = self.pool['nh.clinical.patient.move']
        placement_activity = activity_pool.browse(cr, uid, activity_id,
                                                  context)
        if not placement_activity.data_ref.location_id:
            raise osv.except_osv(
                'Placement Error!',
                'Placement cannot be completed without location')
        res = super(nh_clinical_patient_placement, self).complete(
            cr, uid, activity_id, context)
        placement_activity = activity_pool.browse(
            cr, uid, activity_id, context)
        patient_id = placement_activity.data_ref.patient_id.id
        location_id = placement_activity.data_ref.location_id.id
        spell_id = spell_pool.get_by_patient_id(cr, uid, patient_id,
                                                context=context)
        if not spell_id:
            raise osv.except_osv(
                'Placement Error!',
                'No open spell found for patient_id %s' % patient_id)
        spell_activity_id = spell_pool.browse(
            cr, uid, spell_id, context=context).activity_id.id
        # move to location
        move_activity_id = move_pool.create_activity(
            cr, SUPERUSER_ID,
            {'parent_id': spell_activity_id, 'creator_id': activity_id},
            {'patient_id': patient_id, 'location_id': location_id},
            context=context)
        activity_pool.complete(cr, SUPERUSER_ID, move_activity_id)
        activity_pool.submit(cr, SUPERUSER_ID, spell_activity_id,
                             {'location_id': location_id}, context=context)
        # trigger placement policy activities
        self.trigger_policy(cr, uid, activity_id,
                            location_id=location_id, context=context)
        return res

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data is correct and then calls
        :meth:`submit<activity.nh_activity.submit>`.

        :returns: ``True``
        :rtype: bool
        """
        if vals.get('location_id'):
            location_pool = self.pool['nh.clinical.location']
            available_ids = location_pool.get_available_location_ids(
                cr, uid, ['bed'], context=context)
            if vals['location_id'] not in available_ids:
                raise osv.except_osv(
                    "Patient Placement Error!",
                    "Location id=%s is not available" % vals['location_id'])
        return super(nh_clinical_patient_placement, self).submit(
            cr, uid, activity_id, vals, context)


class nh_clinical_patient_discharge(orm.Model):
    """
    Represents the action of a patient leaving the Hospital after
    completing his or her visit for any reason.
    """
    _name = 'nh.clinical.patient.discharge'
    _inherit = ['nh.activity.data']

    _columns = {
        'patient_id': fields.many2one('nh.clinical.patient',
                                      'Patient', required=True),
        'location_id': fields.many2one('nh.clinical.location',
                                       'Discharged from Location'),
        'discharge_date': fields.datetime('Discharge Date')
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data is correct and then calls
        :meth:`submit<activity.nh_activity.submit>`.

        :returns: ``True``
        :rtype: bool
        """
        data = vals.copy()
        if 'patient_id' in vals:
            spell_pool = self.pool['nh.clinical.spell']
            activity_pool = self.pool['nh.activity']
            spell_id = spell_pool.get_by_patient_id(
                cr, uid, vals['patient_id'], exception='False',
                context=context)
            spell = spell_pool.browse(cr, uid, spell_id, context=context)
            data.update({'location_id': spell.location_id.id})
            activity_pool.write(cr, uid, activity_id,
                                {'parent_id': spell.activity_id.id},
                                context=context)
        else:
            raise osv.except_osv('Discharge Error!',
                                 'Patient required for discharge!')
        return super(nh_clinical_patient_discharge, self).submit(
            cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        creates and completes a new
        :mod:`movement<operations.nh_clinical_patient_move>` to the
        discharge location, which is a virtual location representing
        the patient is no longer in the Hospital.

        It will also complete the current
        :mod:`spell<spell.nh_clinical_spell>`.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_patient_discharge, self).complete(
            cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        location_pool = self.pool['nh.clinical.location']
        activity = activity_pool.browse(cr, SUPERUSER_ID, activity_id,
                                        context=context)

        move_pool = self.pool['nh.clinical.patient.move']
        discharge_location_id = location_pool.search(
            cr, uid, [['code', '=', 'GDL0987654321']])
        if discharge_location_id:
            loc_id = discharge_location_id[0]
        else:
            loc_id = activity.parent_id.data_ref.pos_id.location_id.id
        move_activity_id = move_pool.create_activity(
            cr, uid,
            {'parent_id': activity.parent_id.id, 'creator_id': activity_id},
            {
                'patient_id': activity.data_ref.patient_id.id,
                'location_id': loc_id
            }, context=context)

        activity_pool.complete(cr, uid, move_activity_id, context=context)
        activity_pool.complete(cr, uid, activity.parent_id.id, context=context)
        if activity.data_ref.discharge_date:
            activity_pool.write(
                cr, SUPERUSER_ID, activity.parent_id.id,
                {'date_terminated': activity.data_ref.discharge_date},
                context=context)
        return res

    def cancel(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`cancel<activity.nh_activity.cancel>` and then
        opens (changes state to `started`) the last completed patient
        :mod:`spell<spell.nh_clinical_spell>`.

        It will also create and complete a
        :mod:`movement<operations.nh_clinical_patient_move>` to the
        `bed` location the patient was previously located if it is still
        available. If not, the patient will be moved to the
        corresponding `ward` location parent of that `bed`.

        This operation will kick off a
        :meth:`policy trigger<activity.nh_activity_data.trigger_policy>`
        as this is technically equivalent to an admission back to the
        Hospital.

        :returns: ``True``
        :rtype: bool
        """
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        admission_pool = self.pool['nh.clinical.patient.admission']
        admission_pool.get_last(cr, uid, activity.data_ref.patient_id.id,
                                exception='True', context=context)
        res = super(nh_clinical_patient_discharge, self).cancel(
            cr, uid, activity_id, context=context)
        # reopening spell
        activity_pool.write(
            cr, uid, activity.parent_id.id,
            {'state': 'started', 'date_terminated': False},
            context=context)
        # move to previous location
        move_pool = self.pool['nh.clinical.patient.move']
        move_activity_id = move_pool.create_activity(cr, uid, {
            'parent_id': activity.parent_id.id,
            'creator_id': activity_id
        }, {
            'patient_id': activity.data_ref.patient_id.id,
            'location_id': activity.data_ref.location_id.id
        }, context=context)
        location_pool = self.pool['nh.clinical.location']
        # check if the previous bed is still available
        if activity.data_ref.location_id.usage == 'bed':
            if activity.data_ref.location_id.is_available:
                activity_pool.complete(cr, uid, move_activity_id,
                                       context=context)
                return res

        if activity.data_ref.location_id.usage != 'ward':
            ward_id = location_pool.get_closest_parent_id(
                cr, uid, activity.data_ref.location_id.id, 'ward',
                context=context)
        else:
            ward_id = activity.data_ref.location_id.id

        activity_pool.submit(cr, uid, move_activity_id,
                             {'location_id': ward_id}, context=context)
        activity_pool.complete(cr, uid, move_activity_id, context=context)
        self.trigger_policy(cr, uid, activity_id, location_id=ward_id,
                            context=context)
        return res

    def get_last(self, cr, uid, patient_id, exception=False, context=None):
        """
        Checks if there is a `completed` discharge for the provided
        patient and returns the last one.

        :param exception: 'True' will raise exception when found. 'False'
            when not.
        :type exception: str
        :returns: :mod:`discharge<operations.nh_clinical_patient_discharge>` id
        :rtype: int
        """
        domain = [['patient_id', '=', patient_id],
                  ['data_model', '=', 'nh.clinical.patient.discharge'],
                  ['state', '=', 'completed'],
                  ['parent_id.state', '=', 'completed']]
        activity_pool = self.pool['nh.activity']
        discharge_ids = activity_pool.search(
            cr, uid, domain, order='date_terminated desc, sequence desc',
            context=context)
        if exception:
            if discharge_ids and eval(exception):
                raise osv.except_osv(
                    'Patient Already Discharged!',
                    'Patient with id %s has already been discharged' %
                    patient_id)
            if not discharge_ids and not eval(exception):
                raise osv.except_osv(
                    'Discharge Not Found!',
                    'There is no completed discharge for patient with id %s' %
                    patient_id)
        return discharge_ids[0] if discharge_ids else False


class nh_clinical_patient_admission(orm.Model):
    """
    Represents the action of a patient visiting the Hospital and being
    admitted to one of the Wards.
    """
    _name = 'nh.clinical.patient.admission'
    _inherit = ['nh.activity.data']
    _columns = {
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient',
                                      required=True),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS', required=True),
        'location_id': fields.many2one(
            'nh.clinical.location', 'Admission Location', required=True),
        'start_date': fields.datetime("Admission Start Date"),
        'code': fields.text('Code'),
        'ref_doctor_ids': fields.many2many(
            'nh.clinical.doctor', 'ref_doctor_admission_rel', 'admission_id',
            'doctor_id', "Referring Doctors"),
        'con_doctor_ids': fields.many2many(
            'nh.clinical.doctor', 'con_doctor_admission_rel', 'admission_id',
            'doctor_id', "Consulting Doctors")
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data is correct and then calls
        :meth:`submit<activity.nh_activity.submit>`.

        :returns: ``True``
        :rtype: bool
        """
        if 'patient_id' in vals:
            spell_pool = self.pool['nh.clinical.spell']
            spell_pool.get_by_patient_id(
                cr, uid, vals['patient_id'], exception='True', context=context)
        else:
            raise osv.except_osv('Admission Error!',
                                 'Patient required for admission!')
        return super(nh_clinical_patient_admission, self).submit(
            cr, uid, activity_id, vals, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        creates and starts a new :mod:`spell<spell.nh_clinical_spell>`
        for the selected patient.

        It will also create and complete a
        :mod:`movement<operations.nh_clinical_move>` to the admitted
        location.

        This operation kicks off a
        :meth:`policy trigger<activity.nh_activity_data.trigger_policy>`
        as actions may need to take place after the patient is admitted
        into the Hospital.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_patient_admission, self).complete(
            cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, SUPERUSER_ID, activity_id,
                                        context=context)
        admission = activity.data_ref

        spell_pool = self.pool['nh.clinical.spell']
        spell_activity_id = spell_pool.create_activity(cr, SUPERUSER_ID, {
            'creator_id': activity_id
        }, {
            'patient_id': admission.patient_id.id,
            'location_id': admission.location_id.id,
            'pos_id': admission.pos_id.id,
            'code': admission.code,
            'start_date': admission.start_date,
            'con_doctor_ids': [
                [6, False, [d.id for d in admission.con_doctor_ids]]
            ],
            'ref_doctor_ids': [
                [6, False, [d.id for d in admission.ref_doctor_ids]]
            ]
        }, context=context)
        activity_pool.start(cr, SUPERUSER_ID, spell_activity_id,
                            context=context)
        activity_pool.write(cr, SUPERUSER_ID, activity_id,
                            {'parent_id': spell_activity_id}, context=context)

        move_pool = self.pool['nh.clinical.patient.move']
        move_activity_id = move_pool.create_activity(cr, SUPERUSER_ID, {
            'parent_id': spell_activity_id,
            'creator_id': activity_id
        }, {
            'patient_id': admission.patient_id.id,
            'location_id': admission.location_id.id
        }, context=context)
        activity_pool.complete(cr, SUPERUSER_ID, move_activity_id,
                               context=context)
        # trigger admission policy activities
        self.trigger_policy(
            cr, uid, activity_id, location_id=admission.location_id.id,
            context=context)
        return res

    def cancel(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`cancel<activity.nh_activity.cancel>` and then
        cancels every :class:`activity<activity.nh_activity>` related to
        the admission, including the current patient
        :mod:`spell<spell.nh_clinical_spell>`.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_patient_admission, self).cancel(
            cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        activity_ids = activity_pool.search(cr, uid, [
            ['state', 'not in', ['completed', 'cancelled']],
            ['id', 'child_of', activity.parent_id.id]], context=context)
        for aid in activity_ids:
            activity_pool.cancel(cr, uid, aid, context=context)
        return res

    def get_last(self, cr, uid, patient_id, exception=False, context=None):
        """
        Checks if there is a `completed` admission for the provided
        patient and returns the last one.

        :param exception: 'True' will raise exception when found.
            'False' when not.
        :type exception: str
        :returns: :mod:`admission<operations.nh_clinical_patient_admission>` id
        :rtype: int
        """
        domain = [['patient_id', '=', patient_id],
                  ['data_model', '=', 'nh.clinical.patient.admission'],
                  ['state', '=', 'completed'],
                  ['parent_id.state', '=', 'started']]
        activity_pool = self.pool['nh.activity']
        admission_ids = activity_pool.search(
            cr, uid, domain, order='date_terminated desc, sequence desc',
            context=context)
        if exception:
            if admission_ids and eval(exception):
                raise osv.except_osv(
                    'Patient Already Admitted!',
                    'There is already an active admission '
                    'for patient with id %s' % patient_id)
            if not admission_ids and not eval(exception):
                raise osv.except_osv(
                    'Admission Not Found!',
                    'There is no active admission for patient with id %s' %
                    patient_id)
        return admission_ids[0] if admission_ids else False


class nh_clinical_patient_transfer(orm.Model):
    """
    Represents the action of a patient being moved to a `ward`
    usage :mod:`location<base.nh_clinical_location>` within the
    Hospital.
    """
    _name = 'nh.clinical.patient.transfer'
    _inherit = ['nh.activity.data']
    _columns = {
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient',
                                      required=True),
        'origin_loc_id': fields.many2one('nh.clinical.location',
                                         'Origin Location'),
        'location_id': fields.many2one('nh.clinical.location',
                                       'Transfer Location', required=True)
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data is correct and then calls
        :meth:`submit<activity.nh_activity.submit>`.

        :returns: ``True``
        :rtype: bool
        """
        data = vals.copy()
        if 'patient_id' in vals:
            spell_pool = self.pool['nh.clinical.spell']
            activity_pool = self.pool['nh.activity']
            spell_id = spell_pool.get_by_patient_id(
                cr, uid, vals['patient_id'], exception='False',
                context=context)
            spell = spell_pool.browse(cr, uid, spell_id, context=context)
            data.update({'origin_loc_id': spell.location_id.id})
            activity_pool.write(
                cr, uid, activity_id, {'parent_id': spell.activity_id.id},
                context=context)
        else:
            raise osv.except_osv('Transfer Error!',
                                 'Patient required for transfer!')
        return super(nh_clinical_patient_transfer, self).submit(
            cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        if the destination `ward` usage location is different from where
        the current patient location is located, a new
        :mod:`movement<operations.nh_clinical_patient_move>` is created
        and completed.

        This operation will kick off a
        :meth:`policy trigger<activity.nh_activity_data.trigger_policy>`
        if the movement takes place as this is technically equivalent to
        an admission into the new Ward.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_patient_transfer, self).complete(
            cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, SUPERUSER_ID, activity_id,
                                        context=context)
        transfer = activity.data_ref
        location_pool = self.pool['nh.clinical.location']
        if not location_pool.is_child_of(
                cr, uid, transfer.origin_loc_id.id, transfer.location_id.code,
                context=context):
            move_pool = self.pool['nh.clinical.patient.move']
            move_activity_id = move_pool.create_activity(cr, SUPERUSER_ID, {
                'parent_id': activity.parent_id.id,
                'creator_id': activity_id
            }, {
                'patient_id': transfer.patient_id.id,
                'location_id': transfer.location_id.id
            }, context=context)
            activity_pool.complete(cr, SUPERUSER_ID, move_activity_id,
                                   context=context)
            # trigger transfer policy activities
            self.trigger_policy(
                cr, uid, activity_id, location_id=transfer.location_id.id,
                case=1, context=context)
        return res

    def cancel(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`cancel<activity.nh_activity.cancel>` and then
        if the origin `ward` usage location is different from where the
        current patient location is located, a new
        :mod:`movement<operations.nh_clinical_patient_move>` is created
        and completed.

        If the origin location was of `bed` usage then the movement
        will assign that location back to the patient if it is still
        available.

        This operation will kick off a
        :meth:`policy trigger<activity.nh_activity_data.trigger_policy>`
        if the movement takes place as this is technically equivalent to
        an admission into the new Ward.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_patient_transfer, self).cancel(
            cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        spell_pool = self.pool['nh.clinical.spell']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        transfer = activity.data_ref
        spell_id = spell_pool.get_by_patient_id(
            cr, uid, transfer.patient_id.id, exception='False',
            context=context)
        if activity.parent_id.data_ref.id != spell_id:
            raise osv.except_osv(
                'Integrity Error!',
                'Cannot cancel a transfer from a not active spell!')
        location_pool = self.pool['nh.clinical.location']
        if not location_pool.is_child_of(
                cr, uid, transfer.origin_loc_id.id, transfer.location_id.code,
                context=context):
            move_pool = self.pool['nh.clinical.patient.move']
            move_activity_id = move_pool.create_activity(cr, uid, {
                'parent_id': activity.parent_id.id,
                'creator_id': activity_id
            }, {
                'patient_id': transfer.patient_id.id,
                'location_id': transfer.origin_loc_id.id
            }, context=context)
            location_pool = self.pool['nh.clinical.location']
            # check if the previous bed is still available
            if transfer.origin_loc_id.usage == 'bed' and \
               transfer.origin_loc_id.is_available:
                activity_pool.complete(cr, uid, move_activity_id,
                                       context=context)
                return res

            ward_id = location_pool.get_closest_parent_id(
                cr, uid, transfer.origin_loc_id.id, 'ward', context=context) \
                if transfer.origin_loc_id.usage != 'ward' \
                else transfer.origin_loc_id.id
            activity_pool.submit(cr, uid, move_activity_id,
                                 {'location_id': ward_id}, context=context)
            activity_pool.complete(cr, uid, move_activity_id, context=context)
            self.trigger_policy(cr, uid, activity_id, location_id=ward_id,
                                case=2, context=context)
        return res

    def get_last(self, cr, uid, patient_id, exception=False, context=None):
        """
        Checks if there is a completed transfer for the provided
        patient and returns the last one.

        :param exception: 'True' will raise exception when found.
            'False' when not.
        :type exception: str
        :returns: :mod:`transfer<operations.nh_clinical_patient_transfer>` id
        :rtype: int
        """
        domain = [['patient_id', '=', patient_id],
                  ['data_model', '=', 'nh.clinical.patient.transfer'],
                  ['state', '=', 'completed'],
                  ['parent_id.state', '=', 'started']]
        activity_pool = self.pool['nh.activity']
        transfer_ids = activity_pool.search(
            cr, uid, domain, order='date_terminated desc, sequence desc',
            context=context)
        if exception:
            if transfer_ids and eval(exception):
                raise osv.except_osv(
                    'Patient Already Transferred!',
                    'There is already a transfer '
                    'for patient with id %s' % patient_id)
            if not transfer_ids and not eval(exception):
                raise osv.except_osv(
                    'Transfer Not Found!',
                    'There is no transfer for patient with id %s' % patient_id)
        return transfer_ids[0] if transfer_ids else False


class nh_clinical_patient_follow(orm.Model):
    """
    Represents the action to invite another user to follow a group
    of :mod:`patients<base.nh_clinical_patient>` adding visibility
    for those patients even when the invited user does not have a
    responsibility towards them.
    """
    _name = 'nh.clinical.patient.follow'
    _inherit = ['nh.activity.data']
    _columns = {
        'patient_ids': fields.many2many(
            'nh.clinical.patient', 'follow_patient_rel', 'follow_id',
            'patient_id', 'Patients to Follow', required=True)
    }

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        updates the ``following_ids`` list for the assigned
        :mod:`user<base.res_users>`.

        It will also call
        :meth:`update activity<activity.nh_activity.update_activity>`
        for all not ``completed`` or ``cancelled`` activities related to
        the list of patients.

        :returns: ``True``
        :rtype: bool
        """
        super(nh_clinical_patient_follow, self).complete(
            cr, uid, activity_id, context)
        activity_pool = self.pool['nh.activity']
        user_pool = self.pool['res.users']
        follow_activity = activity_pool.browse(cr, uid, activity_id,
                                               context=context)

        following_ids = []
        for patient in follow_activity.data_ref.patient_ids:
            following_ids.append([4, patient.id])

        if not follow_activity.user_id:
            raise osv.except_osv(
                'Error!',
                'Cannot complete follow activity without an assigned user to '
                'follow the patients')

        res = user_pool.write(
            cr, SUPERUSER_ID, follow_activity.user_id.id,
            {'following_ids': following_ids}, context=context)

        patient_ids = [
            patient.id for patient in follow_activity.data_ref.patient_ids
        ]
        update_activity_ids = activity_pool.search(cr, uid, [
            ['patient_id', 'in', patient_ids],
            ['state', 'not in', ['completed', 'cancelled']]], context=context)
        for activity_id in update_activity_ids:
            activity_pool.update_activity(cr, SUPERUSER_ID, activity_id,
                                          context=context)
        return res


class nh_clinical_patient_unfollow(orm.Model):
    """
    Represents the action to remove followers from a group of
    :mod:`patients<base.nh_clinical_patient>` removing visibility
    for those patients unless the user has a responsibility towards
    them.
    """
    _name = 'nh.clinical.patient.unfollow'
    _inherit = ['nh.activity.data']
    _columns = {
        'patient_ids': fields.many2many(
            'nh.clinical.patient', 'unfollow_patient_rel', 'follow_id',
            'patient_id', 'Patients to stop Following', required=True)
    }

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        removes the ``follower_ids`` list for the selected patients.

        It will also :meth:`cancel<activity.nh_activity.cancel>`
        any number of open (not ``completed`` or ``cancelled``)
        :mod:`follow invitations<operations.nh_clinical_patient_follow>`
        that contain the selected patients.

        :returns: ``True``
        :rtype: bool
        """
        super(nh_clinical_patient_unfollow, self).complete(
            cr, uid, activity_id, context)
        activity_pool = self.pool['nh.activity']
        patient_pool = self.pool['nh.clinical.patient']
        follow_pool = self.pool['nh.clinical.patient.follow']
        unfollow_activity = activity_pool.browse(cr, uid, activity_id,
                                                 context=context)
        patient_ids = [p.id for p in unfollow_activity.data_ref.patient_ids]
        res = patient_pool.write(cr, uid, patient_ids,
                                 {'follower_ids': [[5]]}, context=context)
        update_activity_ids = activity_pool.search(cr, uid, [
            ['patient_id', 'in', patient_ids],
            ['state', 'not in', ['completed', 'cancelled']]], context=context)

        for activity_id in update_activity_ids:
            activity_pool.update_activity(cr, SUPERUSER_ID, activity_id,
                                          context=context)
        # CANCEL PATIENT FOLLOW ACTIVITIES THAT CONTAIN ANY OF THE
        # UNFOLLOWED PATIENTS
        follow_ids = []
        for patient_id in patient_ids:
            follow_ids += follow_pool.search(cr, uid, [
                ['activity_id.create_uid', '=', uid],
                ['patient_ids', 'in', [patient_id]],
                ['activity_id.state', 'not in', ['completed', 'cancelled']]
            ])
        follow_ids = list(set(follow_ids))
        follow_activity_ids = [
            f.activity_id.id for f in follow_pool.browse(
                cr, uid, follow_ids, context=context)
        ]
        for activity_id in follow_activity_ids:
            activity_pool.cancel(cr, uid, activity_id, context=context)
        return res
