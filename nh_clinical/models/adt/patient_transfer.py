import logging

from openerp.osv import orm, fields, osv

_logger = logging.getLogger(__name__)


class nh_clinical_adt_patient_transfer(orm.Model):
    """
    Represents the patient transfer operation in the patient management
    system. (A02 Message)
    """
    _name = 'nh.clinical.adt.patient.transfer'
    _inherit = ['nh.activity.data']
    _description = 'ADT Patient Transfer'
    _columns = {
        'other_identifier': fields.char('Hospital Number', size=100),
        'patient_identifier': fields.char('NHS Number', size=100),
        'original_location': fields.char('Location of Origin', size=256),
        'origin_location_id': fields.many2one('nh.clinical.location',
                                              'Origin Location'),
        'location': fields.char('Location', size=256),
        'location_id': fields.many2one('nh.clinical.location',
                                       'Transfer Location'),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient',
                                      required=True)
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data and then calls
        :meth:`submit<activity.nh_activity.submit>`.

        Creates a new :mod:`spell<spell.nh_clinical_spell>` for the
        provided patient if there is not an open instance related to it
        and an origin location for the transfer was provided.
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
        if not vals.get('location'):
            raise osv.except_osv('Transfer Error!',
                                 'Location must be set for transfer!')
        location_pool = self.pool['nh.clinical.location']
        location_id = location_pool.get_by_code(
            cr, uid, vals['location'], auto_create=True, context=context)

        if vals.get('original_location'):
            olocation_id = location_pool.get_by_code(
                cr, uid, vals.get('original_location'), auto_create=True,
                context=context)
        else:
            olocation_id = False

        patient_pool = self.pool['nh.clinical.patient']
        patient = patient_pool.get_patient_for_identifiers(
            cr, uid,
            hospital_number=vals.get('other_identifier'),
            nhs_number=vals.get('patient_identifier'),
            context=context
        )
        spell_pool = self.pool['nh.clinical.spell']
        activity_pool = self.pool['nh.activity']
        spell_id = spell_pool.get_by_patient_id(
            cr, uid, patient.id, context=context)
        if not spell_id:
            if olocation_id:
                api = self.pool['nh.clinical.api']
                api.admit(
                    cr, uid,
                    vals['other_identifier'],
                    {
                        'location': vals['original_location']
                    },
                    context=context)
                spell_id = spell_pool.get_by_patient_id(
                    cr, uid, patient.id, context=context)
            else:
                raise osv.except_osv(
                    'Transfer Error!',
                    'No origin location provided.')
        spell = spell_pool.browse(cr, uid, spell_id, context=context)
        activity_pool.write(
            cr, uid, activity_id, {'parent_id': spell.activity_id.id},
            context=context)
        data = vals.copy()
        data.update({
            'location_id': location_id,
            'origin_location_id': olocation_id,
            'patient_id': patient.id
        })
        return super(nh_clinical_adt_patient_transfer, self).submit(
            cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        creates and completes a new
        :mod:`transfer<operations.nh_clinical_patient_transfer>` for the
        provided patient.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_adt_patient_transfer, self).complete(
            cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        transfer_pool = self.pool['nh.clinical.patient.transfer']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        transfer = activity.data_ref
        transfer_data = {
            'patient_id': transfer.patient_id.id,
            'location_id': transfer.location_id.id
        }
        transfer_id = transfer_pool.create_activity(
            cr, uid, {'creator_id': activity_id}, transfer_data,
            context=context)
        activity_pool.complete(cr, uid, transfer_id, context=context)
        return res
