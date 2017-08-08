import logging

from openerp.osv import orm, fields, osv

_logger = logging.getLogger(__name__)


class nh_clinical_adt_patient_cancel_admit(orm.Model):
    """
    Represents the cancel admission operation in the patient management
    system. (A11 Message)
    """
    _name = 'nh.clinical.adt.patient.cancel_admit'
    _inherit = ['nh.activity.data']
    _description = 'ADT Cancel Patient Admit'
    _columns = {
        'other_identifier': fields.char('Hospital Number', size=50,
                                        required=True),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient',
                                      required=True),
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
            raise osv.except_osv(
                'Cancel Admit Error!',
                "Patient's Hospital Number must be supplied!"
            )
        patient_pool = self.pool['nh.clinical.patient']
        patient_id = patient_pool.get_patient_for_identifiers(
            cr, uid,
            hospital_number=vals.get('other_identifier'),
            nhs_number=vals.get('patient_identifier'),
            context=context
        )
        spell_pool = self.pool['nh.clinical.spell']
        activity_pool = self.pool['nh.activity']
        spell_id = spell_pool.get_by_patient_id(
            cr, uid, patient_id.id, exception='False', context=context)
        spell = spell_pool.browse(cr, uid, spell_id, context=context)
        activity_pool.write(
            cr, uid, activity_id,
            {
                'parent_id': spell.activity_id.id
            },
            context=context)
        admission_pool = self.pool['nh.clinical.patient.admission']
        admission_id = admission_pool.get_last(
            cr, uid, patient_id.id, exception='False', context=context)
        data = vals.copy()
        data.update(
            {
                'patient_id': patient_id.id,
                'admission_id': admission_id
            }
        )
        return super(nh_clinical_adt_patient_cancel_admit, self) \
            .submit(cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        cancels the last `completed`
        :mod:`admission<operations.nh_clinical_patient_admission>` for
        the provided patient.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_adt_patient_cancel_admit, self).complete(
            cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        activity_pool.cancel(cr, uid, activity.data_ref.admission_id.id,
                             context=context)
        return res
