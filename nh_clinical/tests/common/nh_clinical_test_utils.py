# -*- coding: utf-8 -*-
import uuid

from openerp.models import AbstractModel


class NhClinicalTestUtils(AbstractModel):

    _name = 'nh.clinical.test_utils'

    # Setup methods.
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
        self.other_ward = self.location_model.create(
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
                'name': 'a bed',
                'code': 'a bed',
                'usage': 'bed',
                'parent_id': self.ward.id,
                'type': 'poc',
                'context_ids': [[4, self.eobs_context.id]]
            }
        )
        self.other_bed = self.location_model.create(
            {
                'name': 'b bed',
                'code': 'b_bed',
                'usage': 'bed',
                'parent_id': self.other_ward.id,
                'type': 'poc',
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

    def create_nurse(self, location_id=None):
        if not location_id:
            location_id = self.bed.id
        self.category_model = self.env['res.partner.category']
        self.user_model = self.env['res.users']

        self.nurse_role = \
            self.category_model.search([('name', '=', 'Nurse')])[0]
        # Create nurse and associate them with bed location and nurse role.
        return self.user_model.create({
            'name': 'Nurse',
            'login': uuid.uuid4(),
            'password': 'nurse',
            'category_id': [[4, self.nurse_role.id]],
            'location_ids': [[4, location_id]]
        })

    def create_hca(self, location_id=None):
        if not location_id:
            location_id = self.bed.id
        self.category_model = self.env['res.partner.category']
        self.user_model = self.env['res.users']
        self.hca_role = self.category_model.search([('name', '=', 'HCA')])[0]
        hca = self.user_model.create({
            'name': 'HCA',
            'login': uuid.uuid4(),
            'password': 'hca',
            'category_id': [[4, self.hca_role.id]],
            'location_ids': [[4, location_id]]
        })
        return hca

    def create_doctor(self):
        self.category_model = self.env['res.partner.category']
        self.user_model = self.env['res.users']
        self.doctor_role = \
            self.category_model.search([('name', '=', 'Doctor')])[0]
        # Create doctor and associate them with bed location and doctor role.
        self.doctor = self.user_model.create({
            'name': 'Doctor Acula',
            'login': 'Dr_Acula',
            'password': 'Dr_Acula',
            'category_id': [[4, self.doctor_role.id]],
            'location_ids': [[6, 0, [self.ward.id, self.bed.id]]]
        })

    # Methods for getting references to objects needed for test cases.
    def copy_instance_variables(self, caller):
        """
        Makes a copy of the instance variables on this `nh.clinical.test_utils`
        model and copies them to the passed object.

        The method iterates through the list defined on the first line and
        checks to see if there are any instance variables of that name. If
        there are it takes the value of that instance variable and assigns it
        to the passed object, effectively copying the instance variables.

        This is useful because of the pattern used for test cases. Setup
        methods create records like patients, spells, and observations, and
        assign them to instance variables like `self.spell`. Since moving these
        methods to a single 'test utils' model there is a problem in that all
        these variables are created on the `nh.clinical.test_utils` model
        instead of the test case object that actually needs them. This method
        helps resolve that by making a copy of the instance variables so they
        are available in the test methods themselves.

        :param caller: Any object that can have attributes.
        :type caller: object
        :return:
        """
        instance_variable_names = ['patient', 'spell', 'spell_activity']
        for name in instance_variable_names:
            self.copy_instance_variable_if_exists(caller, name)

    def copy_instance_variable_if_exists(self, caller, variable_name):
        """
        Looks for an instance variable on this model with the passed name.
        If it exists the value is assigned to a new variable of the same name
        on the passed object, effectively copying the instance variable.

        :param caller: Any object that can have attributes.
        :type caller: object
        :param variable_name: Name of the instance variable to copy.
        :type variable_name: str
        :return:
        """
        instance_variable_value = getattr(self, variable_name, None)
        if instance_variable_value:
            setattr(caller, variable_name, instance_variable_value)

    # TODO EOBS-753: Move to patient model? Is just a generally useful method.
    def get_open_activities_for_patient(self, data_model=None, user_id=None):
        """
        Get activity(s) for patient. If a data model is supplied then return
        those only in that data model otherwise just all open activities

        :param data_model: A data model to filter on
        :param user_id: User we want to get activities for
        :return: list of activities
        """
        if not user_id:
            user_id = self.nurse.id
        domain = [
            ['state', 'not in', ['completed', 'cancelled']],
            ['user_ids', 'in', [user_id]],
            ['parent_id', '=', self.spell_activity_id]
        ]
        if data_model:
            domain.append(['data_model', '=', data_model])
        return self.env['nh.activity'].search(domain)

    def get_open_tasks(self, task_type, user_id):
        data_model = 'nh.clinical.notification.{}'.format(task_type)
        return self.get_open_activities_for_patient(data_model, user_id)

    def assert_task_open(self, task_type, user_id):
        open_tasks = self.get_open_tasks(task_type, user_id)
        assert len(open_tasks) > 1
