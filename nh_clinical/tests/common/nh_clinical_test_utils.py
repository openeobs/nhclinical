# -*- coding: utf-8 -*-
import uuid

from openerp.models import AbstractModel


class NhClinicalTestUtils(AbstractModel):

    _name = 'nh.clinical.test_utils'

    # Setup methods
    def setup_ward(self):
        self.create_locations()
        self.create_users()

    def admit_and_place_patient(self, create_placement=True):
        self.setup_ward()
        self.create_patient()
        self.spell = self.admit_patient()
        self.spell_activity_id = self.spell.activity_id.id
        # TODO: Rename variable as it is a spell not an activity.
        self.spell_activity = self.spell.activity_id
        if create_placement:
            self.placement = self.create_placement()
        self.place_patient()

    def create_users(self):
        self.nurse = self.create_nurse()
        self.hca = self.create_hca()
        self.create_doctor()

    def create_patient(self):
        self.patient = self.create_and_register_patient()
        self.patient_id = self.patient.id
        self.hospital_number = self.patient.other_identifier
        return self.patient

    def admit_patient(
            self, hospital_number=None, patient_id=None, location_code=None,
            start_date=None):
        if not hospital_number:
            hospital_number = self.hospital_number
        if not patient_id:
            patient_id = self.patient_id

        creation_values = {
            'location': location_code or self.ward.code
        }
        if start_date:
            creation_values['start_date'] = start_date

        self.api_model = self.env['nh.clinical.api']
        self.api_model.admit(hospital_number, creation_values)
        self.spell_model = self.env['nh.clinical.spell']
        return self.spell_model.search([('patient_id', '=', patient_id)])[0]

    def create_placement(self, patient_id=None, location_id=None):
        if not patient_id:
            patient_id = self.patient_id
        if not location_id:
            location_id = self.ward.id
        self.placement_model = self.env['nh.clinical.patient.placement']
        return self.placement_model.create_activity({}, {
            'suggested_location_id': location_id,
            'patient_id': patient_id
        })

    def create_and_register_patient(self):
        self.api_model = self.env['nh.clinical.api']
        self.patient_model = self.env['nh.clinical.patient']

        hospital_number = str(uuid.uuid4())
        patient_id = self.api_model.sudo().register(
            hospital_number,
            {
                'family_name': 'Testersen',
                'given_name': 'Test',
                'patient_identifier': str(uuid.uuid4())
            }
        )
        return self.patient_model.browse(patient_id)

    def place_patient(
            self, location_id=None, placement_activity_id=None):
        if not location_id:
            location_id = self.bed.id
        if not placement_activity_id:
            activity_model = self.env['nh.activity']
            domain = [
                ('data_model', '=', 'nh.clinical.patient.placement'),
                ('patient_id', '=', self.patient.id),
                ('state', 'not in', ['completed', 'cancelled'])
            ]
            placement_activities = activity_model.search(domain)
            placement_activity_id = placement_activities[0].id
        self.activity_model = self.env['nh.activity']
        self.activity_pool = self.pool['nh.activity']
        self.activity_pool.submit(
            self.env.cr, self.env.uid,
            placement_activity_id, {'location_id': location_id}
        )
        self.activity_pool.complete(
            self.env.cr, self.env.uid, placement_activity_id
        )

    def discharge_patient(self, hospital_number=None):
        hospital_number = hospital_number or self.hospital_number
        api_model = self.env['nh.clinical.api']
        api_model.discharge(hospital_number, {
            'location': 'DISL'
        })

    def transfer_patient(self, location_code=None, hospital_number=None):
        hospital_number = hospital_number or self.hospital_number
        location_code = location_code or self.other_ward.code

        api_model = self.env['nh.clinical.api']
        api_model.transfer(hospital_number, {
            'location': location_code
        })

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
        # nh.eobs.api not available to this module
        self.api_model = self.env['nh.clinical.api']

        self.patient = self.patient_model.create({
            'given_name': 'Jon',
            'family_name': 'Snow',
            'patient_identifier': str(uuid.uuid4()),
            'other_identifier': str(uuid.uuid4())
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

    def create_hospital_and_pos(self):
        self.location_model = self.env['nh.clinical.location']
        self.pos_model = self.env['nh.clinical.pos']

        self.hospital = self.location_model.create({
            'name': 'Your Hospital',
            'code': 'YH01',
            'type': 'pos',
            'usage': 'hospital'
        })
        self.company = \
            self.env['ir.model.data'].get_object('base', 'main_company')
        self.pos = self.pos_model.create({
            'name': 'Your Hospital',
            'location_id': self.hospital.id,
            'company_id': self.company.id
        })

    def create_locations(self):
        self.create_hospital_and_pos()
        self.location_model = self.env['nh.clinical.location']

        self.ward = self.create_location('ward', self.hospital.id)
        self.other_ward = self.create_location('ward', self.hospital.id)

        self.bed = self.create_location('bed', self.ward.id)
        self.other_bed = self.create_location('bed', self.other_ward.id)
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

    def create_location(self, usage='bed', parent=None, name=None):
        if not parent:
            parent = self.ward.id
        if not name:
            name = uuid.uuid4()
        return self.location_model.create(
            {
                'code': str(uuid.uuid4()),
                'name': name,
                'usage': usage,
                'parent_id': parent,
                'type': 'poc',
            }
        )

    def _create_user(self, category, location_id=None, allocate=True):
        """
        Creates a user.

        :param category: Must be an existing category name like 'Nurse' or
        'HCA'.
        :param location_id:
        :param allocate:
        :return:
        """
        self.category_model = self.env['res.partner.category']
        self.user_model = self.env['res.users']

        self.user_role = \
            self.category_model.search([('name', '=', category)])[0]
        # Create nurse and associate them with bed location and nurse role.
        creation_values = {
            'name': category,
            'login': str(uuid.uuid4()),
            'password': category,
            'category_id': [[4, self.user_role.id]],
        }
        if allocate is True:
            creation_values['location_ids'] = [(4, location_id or self.bed.id)]
        return self.user_model.create(creation_values)

    def create_nurse(self, location_id=None, allocate=True):
        return self._create_user('Nurse', location_id, allocate)

    def create_hca(self, location_id=None, allocate=True):
        return self._create_user('HCA', location_id, allocate)

    def create_doctor(self, location_ids=None):
        if location_ids is not None and not isinstance(location_ids, list):
            raise TypeError("Location IDs must be a list.")
        self.category_model = self.env['res.partner.category']
        self.user_model = self.env['res.users']
        self.doctor_role = \
            self.category_model.search([('name', '=', 'Doctor')])[0]

        if not location_ids:
            location_ids = [self.ward.id, self.bed.id]
        # Create doctor and associate them with bed location and doctor role.
        self.doctor = self.user_model.create({
            'name': 'Doctor Acula',
            'login': 'Dr_Acula',
            'password': 'Dr_Acula',
            'category_id': [[4, self.doctor_role.id]],
            'location_ids': [[6, 0, location_ids]]
        })

    def create_shift_coordinator(self, location_id=None):
        if not location_id:
            location_id = self.ward.id
        self.category_model = self.env['res.partner.category']
        self.user_model = self.env['res.users']
        self.shift_coordinator_role = \
            self.category_model.search([('name', '=', 'Shift Coordinator')])[0]
        shift_coordinator = self.user_model.create({
            'name': 'Anita Co\'Ordon',
            'login': str(uuid.uuid4()),
            'password': 'coordon-anita',
            'category_id': [[4, self.shift_coordinator_role.id]],
            'location_ids': [[6, 0, [location_id]]]
        })
        return shift_coordinator

    def create_senior_manager(self):
        self.category_model = self.env['res.partner.category']
        self.user_model = self.env['res.users']
        self.senior_manager_role = \
            self.category_model.search([('name', '=', 'Senior Manager')])[0]
        self.senior_manager = self.user_model.create({
            'name': 'Senor Manager',
            'login': 'snr.manager',
            'password': 'snr.manager',
            'category_id': [[4, self.senior_manager_role.id]],
            'location_ids': [[6, 0, [self.ward.id]]]
        })

    def create_system_admin(self):
        self.category_model = self.env['res.partner.category']
        self.user_model = self.env['res.users']
        self.system_admin_role = \
            self.category_model.search(
                [
                    ('name', '=', 'System Administrator')
                ]
            )[0]
        self.system_admin = self.user_model.create({
            'name': 'System admin',
            'login': 'system.admin',
            'password': 'system.admin',
            'category_id': [[4, self.system_admin_role.id]],
            'location_ids': [[6, 0, [self.ward.id]]]
        })

    def create_adt_user(self, location_id=None, allocate=False):
        return self._create_user('System Administrator', location_id, allocate)

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
        instance_variable_names = [
            'patient', 'spell', 'spell_activity', 'hca', 'nurse', 'doctor',
            'company', 'hospital', 'pos', 'ward'
        ]
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

    def get_open_tasks(self, task_type, user_id=None):
        """
        Get all open tasks of a particular type.

        :param task_type:
        :type task_type: str
        :param user_id:
        :return:
        """
        data_model = 'nh.clinical.notification.{}'.format(task_type)
        return self.get_open_activities_for_patient(data_model, user_id)

    def get_latest_open_task(self, user_id=None):
        """
        Get the most recently created, currently open task
        (activity of a notification).

        :param user_id:
        :return:
        """
        if not user_id:
            user_id = self.nurse.id
        domain = [
            ('state', 'not in', ['completed', 'cancelled']),
            ('data_model', 'like', 'nh.clinical.notification'),
            ('parent_id', '=', self.spell_activity_id),
            ('user_ids', 'in', [user_id])
        ]
        return self.env['nh.activity'].search(
            domain, order='create_date desc, id desc'
        )[0]

    def get_open_task_triggered_by(self, triggering_activity_id):
        """
        Returns any task triggered by the passed activity.

        :param triggering_activity_id:
        :type triggering_activity_id: int
        :return: nh.activity or None
        """
        domain = [
            ('creator_id', '=', triggering_activity_id),
            ('data_model', 'like', 'nh.clinical.notification'),
            ('parent_id', '=', self.spell_activity_id)
        ]
        tasks = self.env['nh.activity'].search(
            domain, order='create_date desc, id desc'
        )
        return tasks if tasks else None

    def assert_task_open(self, task_type, user_id=None):
        open_tasks = self.get_open_tasks(task_type, user_id)
        if not len(open_tasks) > 1:
            raise AssertionError("No open tasks.")

    def browse_ref(self, xid):
        """
        Returns a record object for the provided :term:`external identifier`.

        Copied from :class:`~openerp.tests.common.BaseCase`.

        :param xid: fully-qualified :term:`external identifier`, in the form
                    :samp:`{module}.{identifier}`
        :raise: ValueError if not found
        :returns: :class:`~openerp.models.BaseModel`
        """
        if '.' not in xid:
            message = "this method requires a fully qualified parameter, " \
                      "in the following form: 'module.identifier'"
            raise ValueError(message)
        module, xid = xid.split('.')
        return self.env['ir.model.data'].get_object(module, xid)
