import logging

from openerp import SUPERUSER_ID
from openerp.osv import orm, fields, osv

_logger = logging.getLogger(__name__)


class nh_clinical_adt_patient_merge(orm.Model):
    """
    Represents the patient merge operation in the patient management
    system. (A40 Message)
    Merges a patient into another patient making the resulting patient
    own all activities.
    """
    _name = 'nh.clinical.adt.patient.merge'
    _inherit = ['nh.activity.data']
    _description = 'ADT Patient Merge'
    _columns = {
        'from_identifier': fields.char('Source Identifier', size=100),
        'source_patient_id': fields.many2one('nh.clinical.patient',
                                             'Source Patient'),
        'into_identifier': fields.char('Destination Identifier', size=100),
        'dest_patient_id': fields.many2one('nh.clinical.patient',
                                           'Destination Patient'),
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data and then calls
        :meth:`submit<activity.nh_activity.submit>`.

        :returns: ``True``
        :rtype: bool
        """
        patient_pool = self.pool['nh.clinical.patient']
        data = vals.copy()
        if data.get('from_identifier'):
            from_patient = patient_pool.get_patient_for_identifiers(
                cr, uid,
                hospital_number=data.get('from_identifier'),
                context=context
            )
            data.update({'source_patient_id': from_patient.id})
        if data.get('into_identifier'):
            into_patient = patient_pool.get_patient_for_identifiers(
                cr, uid,
                hospital_number=data.get('into_identifier'),
                context=context
            )
            data.update({'dest_patient_id': into_patient.id})
        return super(nh_clinical_adt_patient_merge, self) \
            .submit(cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        adds every piece of information that the source patient has and
        the destination patient lacks into the destination patient.

        The destination patient ends up being linked to all the
        :class:`activities<activity.nh_activity>` both patients were
        linked to.

        :returns: ``True``
        :rtype: bool
        """
        res = {}
        activity_pool = self.pool['nh.activity']
        merge_activity = activity_pool.browse(
            cr, SUPERUSER_ID, activity_id, context=context)
        if not merge_activity.data_ref.source_patient_id:
            raise osv.except_osv(
                'Patient Merge Error!',
                "Source patient not found in submitted data!")
        if not merge_activity.data_ref.dest_patient_id:
            raise osv.except_osv(
                'Patient Merge Error!',
                "Destination patient not found in submitted data!")
        super(nh_clinical_adt_patient_merge, self).complete(
            cr, uid, activity_id, context=context)
        patient_pool = self.pool['nh.clinical.patient']
        from_id = merge_activity.data_ref.source_patient_id.id
        into_id = merge_activity.data_ref.dest_patient_id.id

        for model_name in self.pool.models.keys():
            model_pool = self.pool[model_name]
            if model_name.startswith("nh.clinical") and model_pool._auto and \
                'patient_id' in model_pool._columns.keys() and \
                model_name != self._name and \
                model_name != 'nh.clinical.notification' and model_name != \
                    'nh.clinical.patient.observation':
                ids = model_pool.search(
                    cr, uid, [('patient_id', '=', from_id)], context=context)
                if ids:
                    model_pool.write(cr, uid, ids, {'patient_id': into_id},
                                     context=context)
        activity_ids = activity_pool.search(
            cr, uid, [('patient_id', '=', from_id)], context=context)
        activity_pool.write(cr, uid, activity_ids,
                            {'patient_id': into_id}, context=context)
        from_data = patient_pool.read(cr, uid, from_id, context)
        into_data = patient_pool.read(cr, uid, into_id, context)
        vals_into = {}
        for key, value in from_data.iteritems():
            if not value:
                continue
            if value and into_data[key] and value != into_data[key]:
                pass
            if value and not into_data[key]:
                if '_id' == key[-3:]:
                    vals_into.update({key: value[0]})
                else:
                    vals_into.update({key: value})
        res['merge_into_update'] = patient_pool.write(
            cr, uid, into_id, vals_into, context=context)
        res['merge_from_deactivate'] = patient_pool.write(
            cr, uid, from_id, {'active': False}, context=context)
        activity_pool.write(cr, uid, activity_id, {'patient_id': into_id},
                            context=context)
        return res
