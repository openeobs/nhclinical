import logging
from datetime import datetime as dt
from openerp.osv import orm, fields, osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

_logger = logging.getLogger(__name__)


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
        'location_id': fields.many2one('nh.clinical.location',
                                       'Pre-Discharge Location'),
        'discharge_date': fields.datetime('Discharge Date'),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient',
                                      required=True)
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
        if not user.pos_ids:
            raise osv.except_osv('POS Missing Error!',
                                 "POS location is not set for user.login = %s!"
                                 % user.login)
        data = vals.copy()
        patient_pool = self.pool['nh.clinical.patient']
        patient_id = patient_pool.get_patient_id_for_identifiers(
            cr, uid,
            hospital_number=vals.get('other_identifier'),
            nhs_number=vals.get('patient_identifier'),
            context=context
        )
        if vals.get('discharge_date'):
            discharge_date = vals.get('discharge_date')
        else:
            discharge_date = dt.now().strftime(DTF)

        spell_pool = self.pool['nh.clinical.spell']
        activity_pool = self.pool['nh.activity']
        spell_id = spell_pool.get_by_patient_id(
            cr, uid, patient_id.id, context=context)
        if not spell_id:
            if not vals.get('location'):
                raise osv.except_osv(
                    'Discharge Error!',
                    'Missing location and patient is not admitted!')
            discharged = activity_pool.search(
                cr, uid,
                [
                    ['data_model', '=', 'nh.clinical.spell'],
                    ['patient_id', '=', patient_id.id],
                    ['state', '=', 'completed']
                ], context=context)
            if discharged:
                raise osv.except_osv(
                    'Discharge Error!',
                    'Patient is already discharged!'
                )
            _logger.warn("Patient admitted from a discharge call!")
            location_pool = self.pool['nh.clinical.location']
            location_id = location_pool.get_by_code(
                cr, uid, vals['location'], auto_create=True, context=context)
            location = location_pool.browse(
                cr, uid, location_id, context=context)
            data.update({'location_id': location_id})
            admission_pool = self.pool['nh.clinical.patient.admission']
            admission_data = {
                'pos_id': location.pos_id.id,
                'patient_id': patient_id.id,
                'location_id': location_id,
            }
            admission_id = admission_pool.create_activity(
                cr, uid, {'creator_id': activity_id}, admission_data,
                context=context)
            activity_pool.complete(cr, uid, admission_id, context=context)
            spell_id = spell_pool.get_by_patient_id(
                cr, uid, patient_id.id, exception='False', context=context)
        spell = spell_pool.browse(cr, uid, spell_id, context=context)
        data.update(
            {
                'patient_id': patient_id.id,
                'discharge_date': discharge_date
            }
        )
        activity_pool.write(
            cr, uid, activity_id,
            {
                'parent_id': spell.activity_id.id
            },
            context=context)
        return super(nh_clinical_adt_patient_discharge, self) \
            .submit(cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        creates and completes a new
        :mod:`discharge<operations.nh_clinical_patient_discharge>` for
        the provided patient.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_adt_patient_discharge, self).complete(
            cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        discharge_pool = self.pool['nh.clinical.patient.discharge']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        discharge_data = {
            'patient_id': activity.data_ref.patient_id.id,
            'discharge_date': activity.data_ref.discharge_date
        }
        discharge_id = discharge_pool.create_activity(
            cr, uid, {'creator_id': activity_id}, discharge_data,
            context=context)
        activity_pool.complete(cr, uid, discharge_id, context=context)
        return res
