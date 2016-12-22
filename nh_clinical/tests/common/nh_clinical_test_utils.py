# -*- coding: utf-8 -*-
from openerp.models import AbstractModel


class NhClinicalTestUtils(AbstractModel):

    _name = 'nh.clinical.test_utils'

    # Setup methods
    def create_patient_and_spell(self):
        """
        Create patient and spell.
        Assigns various objects to instance variables.

        :param self:
        :return:
        """
        self.patient_model = self.env['nh.clinical.patient']
        self.spell_model = self.env['nh.clinical.spell']
        self.activity_model = self.env['nh.activity']
        self.activity_pool = self.pool['nh.activity']
        self.ews_model = self.env['nh.clinical.patient.observation.ews']
        # nh.eobs.api not available to this module
        self.api_model = self.env['nh.clinical.api']

        self.patient = self.patient_model.create({
            'given_name': 'Jon',
            'family_name': 'Snow',
            'patient_identifier': 'a_patient_identifier',
            'other_identifier': 'another_identifier'
        })

        self.spell_activity_id = self.spell_model.create_activity(
            {},
            {'patient_id': self.patient.id, 'pos_id': 1}
        )

        self.spell_activity = \
            self.activity_model.browse(self.spell_activity_id)

        # Fails in spell.get_patient_by_id() if not started.
        self.activity_pool.start(self.env.cr, self.env.uid,
                                 self.spell_activity_id)

        self.spell = self.spell_activity.data_ref

    def search_for_hospital_and_pos(self):
        self.location_model = self.env['nh.clinical.location']
        self.pos_model = self.env['nh.clinical.pos']

        hospital_search = self.location_model.search(
            [('usage', '=', 'hospital')]
        )
        if hospital_search:
            self.hospital = hospital_search[0]
        else:
            raise ValueError('Could not find hospital ID')
        pos_search = self.pos_model.search(
            [('location_id', '=', self.hospital.id)]
        )
        if pos_search:
            self.pos = pos_search[0]
        else:
            raise ValueError('Could not find POS with location ID of hospital')

    def create_locations(self):
        self.location_model = self.env['nh.clinical.location']
        self.context_pool = self.env['nh.clinical.context']

        self.ward = self.location_model.create(
            {
                'name': 'Ward A',
                'code': 'WA',
                'usage': 'ward',
                'parent_id': self.hospital.id,
                'type': 'poc'
            }
        )
        self.location_model.create(
            {
                'name': 'Ward B',
                'code': 'WB',
                'usage': 'ward',
                'parent_id': self.hospital.id,
                'type': 'poc'
            }
        )
        self.eobs_context = self.context_pool.search(
            [['name', '=', 'eobs']]
        )[0]
        self.bed = self.location_model.create(
            {
                'name': 'a bed', 'code': 'a bed', 'usage': 'bed',
                'parent_id': self.ward.id, 'type': 'poc',
                'context_ids': [[4, self.eobs_context.id]]
            }
        )
        self.associate_admin_with_pos()

    def associate_admin_with_pos(self):
        self.user_model = self.env['res.users']

        self.admin = self.user_model.browse(self.env.uid)
        self.admin.write(
            {
                'pos_id': self.pos.id,
                'pos_ids': [[4, self.pos.id]]
            }
        )

    def create_nurse(self):
        self.category_model = self.env['res.partner.category']
        self.user_model = self.env['res.users']

        self.nurse_role = \
            self.category_model.search([('name', '=', 'Nurse')])[0]
        # Create nurse and associate them with bed location and nurse role.
        self.nurse = self.user_model.create({
            'name': 'Jon',
            'login': 'iknownothing',
            'password': 'atall',
            'category_id': [[4, self.nurse_role.id]],
            'location_ids': [[4, self.bed.id]]
        })

    def create_doctor(self):
        self.category_model = self.env['res.partner.category']
        self.user_model = self.env['res.users']

        self.doctor_role = \
            self.category_model.search([('name', '=', 'Doctor')])[0]
        # Create doctor and associate them with bed location and doctor role.
        self.doctor = self.user_model.create({
            'name': 'Doctor Acula',
            'login': 'doctor',
            'password': 'doctor',
            'category_id': [[4, self.doctor_role.id]],
            'location_ids': [[6, 0, [self.ward.id, self.bed.id]]]
        })
