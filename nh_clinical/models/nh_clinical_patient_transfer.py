# -*- coding: utf-8 -*-
import logging

from openerp import SUPERUSER_ID, api
from openerp.osv import orm, fields, osv

_logger = logging.getLogger(__name__)


class NhClinicalPatientTransfer(orm.Model):
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
        return super(NhClinicalPatientTransfer, self).submit(
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
        res = super(NhClinicalPatientTransfer, self).complete(
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
        res = super(NhClinicalPatientTransfer, self).cancel(
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
        :returns: :mod:`transfer<operations.NhClinicalPatientTransfer>` id
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

    @api.model
    def patient_was_transferred_after_date(self, patient_id, date):
        """
        Check if a patient transfer occurred some time after the given date.

        :param patient_id:
        :type patient_id: int
        :param date:
        :type date: str
        :return:
        :rtype: bool
        """
        last_transfer_activity_id = self.get_last(patient_id)
        activity_model = self.env['nh.activity']
        last_transfer = activity_model.browse(last_transfer_activity_id)
        if not last_transfer:
            return False
        # `date_started` doesn't appear to be populated by so can't use it.
        return last_transfer.date_terminated >= date
