import logging

from openerp import SUPERUSER_ID
from openerp.osv import orm, fields, osv

_logger = logging.getLogger(__name__)


class nh_clinical_adt_spell_update(orm.Model):
    """
    Represents the admission update operation in the patient management
    system. (A08 Message)
    """
    _name = 'nh.clinical.adt.spell.update'
    _inherit = ['nh.activity.data']
    _description = 'ADT Spell Update'
    _columns = {
        'location_id': fields.many2one('nh.clinical.location',
                                       'Admission Location'),
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient',
                                      required=True),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS', required=True),
        'location': fields.char('Location', size=256),
        'code': fields.char("Code", size=256),
        'start_date': fields.datetime("Admission Date"),
        'other_identifier': fields.char('Hospital Number', size=100),
        'patient_identifier': fields.char('NHS Number', size=100),
        'doctors': fields.text("Doctors"),
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data and then calls
        :meth:`submit<activity.nh_activity.submit>`.

        If a :mod:`location<base.nh_clinical_location>` of `ward` usage
        with the provided code does not exist, it will create a new one.

        Due to this behaviour the user submitting the data must be
        related to a :mod:`point of service<base.nh_clinical_pos>`
        linked to a valid :mod:`location<base.nh_clinical_location>`
        instance of `pos` type, as new Wards will need to be assigned
        to a point of service.

        :returns: ``True``
        :rtype: bool
        """
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        if not user.pos_ids:
            raise osv.except_osv('POS Missing Error!',
                                 "POS location is not set for user.login = %s!"
                                 % user.login)
        if not vals.get('location'):
            raise osv.except_osv('Update Error!',
                                 'Location must be set for spell update!')
        location_pool = self.pool['nh.clinical.location']
        location_id = location_pool.get_by_code(
            cr, uid, vals['location'], auto_create=True, context=context)
        location = location_pool.browse(cr, uid, location_id, context=context)
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
            raise osv.except_osv(
                'Update Error!',
                'The patient does not have an open spell!')
        spell = spell_pool.browse(cr, uid, spell_id, context=context)
        activity_pool.write(
            cr, uid, activity_id,
            {
                'parent_id': spell.activity_id.id
            },
            context=context)
        data = vals.copy()
        data.update({
            'location_id': location_id,
            'patient_id': patient.id,
            'pos_id': location.pos_id.id
        })
        return super(nh_clinical_adt_spell_update, self) \
            .submit(cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Overwrites the target :mod:`spell<spell.nh_clinical_spell>`
        information and then calls
        :meth:`complete<activity.nh_activity.complete>`.

        If location information needs to be updated a new instance of
        :mod:`movement<operations.nh_clinical_patient_move>` is created
        and completed.

        If the new location is located in a different Ward than the
        current spell location, a
        :meth:`policy trigger<activity.nh_activity_data.trigger_policy>`
        will be kicked off. As that is technically a transfer movement.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_adt_spell_update, self) \
            .complete(cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        update = activity.data_ref
        update_data = {
            'pos_id': update.pos_id.id,
            'code': update.code,
            'start_date': update.start_date
        }
        if update.doctors:
            doctor_pool = self.pool['nh.clinical.doctor']
            update_data.update({'doctors': update.doctors})
            doctor_pool.evaluate_doctors_dict(
                cr, uid, update_data, context=context)
            del update_data['doctors']
        else:
            update_data.update(
                {
                    'con_doctor_ids': [[5]],
                    'ref_doctor_ids': [[5]]
                }
            )
        activity_pool.submit(
            cr, uid, activity.parent_id.id, update_data, context=context)
        location_pool = self.pool['nh.clinical.location']
        if not location_pool.is_child_of(
                cr, uid,
                activity.parent_id.location_id.id,
                update.location,
                context=context):
            move_pool = self.pool['nh.clinical.patient.move']
            move_activity_id = move_pool.create_activity(
                cr, SUPERUSER_ID,
                {
                    'parent_id': activity.parent_id.id,
                    'creator_id': activity_id
                },
                {
                    'patient_id': update.patient_id.id,
                    'location_id': update.location_id.id
                },
                context=context)
            activity_pool.complete(
                cr, SUPERUSER_ID, move_activity_id, context=context)
            # trigger transfer policy activities
            self.trigger_policy(
                cr, uid, activity_id,
                location_id=update.location_id.id,
                context=context)
        return res
