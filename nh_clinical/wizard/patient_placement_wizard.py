# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
import logging

from openerp.osv import orm, fields

_logger = logging.getLogger(__name__)


class nh_clinical_patient_placement_wizard(orm.TransientModel):
    _name = 'nh.clinical.patient.placement.wizard'
    _columns = {
        'placement_ids': fields.many2many('nh.clinical.patient.placement',
                                          'placement_wiz_rel', 'placement_id',
                                          'wiz_id', 'Placements'),
        'recent_placement_ids': fields.many2many(
            'nh.clinical.patient.placement', 'recent_placement_wiz_rel',
            'placement_id', 'wiz_id', 'Recent Placements'),
    }

    def _get_placement_ids(self, cr, uid, context=None):
        domain = [('state', 'in', ['draft', 'scheduled', 'started'])]
        placement_pool = self.pool['nh.clinical.patient.placement']
        placement_ids = placement_pool.search(
            cr, uid, domain, context=context
        )
        return placement_ids

    def _get_recent_placement_ids(self, cr, uid, context=None):
        domain = [('state', 'in', ['completed'])]
        placement_pool = self.pool['nh.clinical.patient.placement']
        placement_ids = placement_pool.search(
            cr, uid, domain, limit=3, order="date_terminated desc",
            context=context
        )
        return placement_ids

    _defaults = {
        'placement_ids': _get_placement_ids,
        'recent_placement_ids': _get_recent_placement_ids,
    }

    def _place_patients(self, cr, uid, activity_id, location_id, context=None):
        activity_pool = self.pool['nh.activity']
        activity_pool.start(cr, uid, activity_id, context)
        activity_pool.submit(cr, uid, activity_id,
                             {'location': location_id}, context)
        activity_pool.complete(cr, uid, activity_id, context)

    def _get_placements(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids[0], context)
        return wizard.placement_ids

    def _get_place_patients(self, cr, uid, ids, context=None):
        placements = self._get_placements(cr, uid, ids, context=context)
        for placement in placements:
            if placement.location_id:
                self._place_patients(
                    cr, uid, placement.activity_id.id,
                    placement.location_id.id, context=context
                )

    def apply(self, cr, uid, ids, context=None):
        self._get_place_patients(cr, uid, ids, context)
        self.write(cr, uid, ids, {
            'placement_ids': [(6, 0, self._get_placement_ids(cr, uid))],
            'recent_placement_ids': [
                (6, 0, self._get_recent_placement_ids(cr, uid))
            ]
        }, context)
        aw = {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': ids[0],
            'view_type': "form",
            'view_mode': "form",
            'target': "inline",
        }
        return aw
