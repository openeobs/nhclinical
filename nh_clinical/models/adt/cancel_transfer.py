import logging

from openerp.osv import orm, fields

_logger = logging.getLogger(__name__)


class nh_clinical_adt_patient_cancel_transfer(orm.Model):
    """
    Represents the cancel transfer operation in the patient management
    system. (A12 Message)
    """
    _name = 'nh.clinical.adt.patient.cancel_transfer'
    _inherit = ['nh.activity.data']
    _description = 'ADT Cancel Patient Transfer'
    _columns = {
        'other_identifier': fields.char('Hospital Number', size=100),
        'patient_identifier': fields.char('NHS Number', size=100),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient',
                                      required=True),
        'transfer_id': fields.many2one('nh.activity', 'Transfer Activity')
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data is correct, finding the last
        `completed` instance of
        :mod:`transfer<operations.nh_clinical_patient_transfer>`
        and then calls :meth:`submit<activity.nh_activity.submit>`.

        :returns: ``True``
        :rtype: bool
        """
        patient_pool = self.pool['nh.clinical.patient']
        patient = patient_pool.get_patient_id_for_identifiers(
            cr, uid,
            hospital_number=vals.get('other_identifier'),
            nhs_number=vals.get('patient_identifier'),
            context=context
        )
        transfer_pool = self.pool['nh.clinical.patient.transfer']
        transfer_id = transfer_pool.get_last(
            cr, uid, patient.id, exception='False', context=context)
        data = vals.copy()
        data.update(
            {'patient_id': patient.id,
             'transfer_id': transfer_id
             }
        )
        return super(nh_clinical_adt_patient_cancel_transfer, self).submit(
            cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        cancels the last `completed`
        :mod:`transfer<operations.nh_clinical_patient_transfer>` for the
        provided patient.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_adt_patient_cancel_transfer, self).complete(
            cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        cancel = activity.data_ref
        activity_pool.cancel(cr, uid, cancel.transfer_id.id, context=context)
        activity_pool.write(
            cr, uid, activity_id,
            {
                'parent_id': cancel.transfer_id.parent_id.id
            },
            context=context)
        return res
