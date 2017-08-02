import logging
from openerp.osv import orm, fields

_logger = logging.getLogger(__name__)


class nh_clinical_adt_patient_cancel_discharge(orm.Model):
    """
    Represents the cancel discharge operation in the patient management
    system. (A13 Message)
    """
    _name = 'nh.clinical.adt.patient.cancel_discharge'
    _inherit = ['nh.activity.data']
    _description = 'ADT Cancel Patient Discharge'
    _columns = {
        'other_identifier': fields.char('Hospital Number', size=50,
                                        required=True),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient',
                                      required=True),
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
        patient_pool = self.pool['nh.clinical.patient']
        patient_id = patient_pool.get_patient_id_for_identifiers(
            cr, uid,
            hospital_number=vals.get('other_identifier'),
            nhs_number=vals.get('patient_identifier'),
            context=context
        )
        discharge_pool = self.pool['nh.clinical.patient.discharge']
        discharge_id = discharge_pool.get_last(
            cr, uid, patient_id.id, exception='False', context=context)
        data = vals.copy()
        data.update(
            {
                'patient_id': patient_id.id,
                'discharge_id': discharge_id
            }
        )
        return super(nh_clinical_adt_patient_cancel_discharge, self) \
            .submit(cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        cancels the last `completed`
        :mod:`discharge<operations.nh_clinical_patient_discharge>` for
        the provided patient.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_adt_patient_cancel_discharge, self) \
            .complete(cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        activity_pool.cancel(
            cr, uid, activity.data_ref.discharge_id.id, context=context)
        activity_pool.write(
            cr, uid, activity_id,
            {
                'parent_id': activity.data_ref.discharge_id.parent_id.id
            },
            context=context)
        return res
