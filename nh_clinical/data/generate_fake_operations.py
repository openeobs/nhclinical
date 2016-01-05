from xml.etree.ElementTree import Element, SubElement, Comment, dump, parse
import random
import re


class OperationsGenerator(object):

    def __init__(self, ward_file):

        # Create root element
        self.root = Element('openerp')

        # Create data inside root element
        self.data = SubElement(self.root, 'data', {'noupdate': '1'})

        # Read the patient XML file
        patient_data = parse('ward_{0}/demo_patients.xml'.format(ward_file))
        self.demo_patients = patient_data.findall('data')[0].findall('record')

        # List of time periods to randomly offset admissions
        self.admit_offset_list = ['-1', '-2']
        self.admit_date_eval_string = '(datetime.now() + timedelta({0}))' \
                                      '.strftime(\'%Y-%m-%d 00:00:00\')'

        # Regex to use to get the ID for a patient from id attribute on record
        patient_id_regex_string = 'nhc_demo_patient_(\d+)'
        ward_regex_string = '(nhc_def_conf_location_w\w)'
        self.patient_id_regex = re.compile(patient_id_regex_string)
        self.ward_regex = re.compile(ward_regex_string)

        # Generate the patient admissions
        self.admit_patients()

        # Pretty Print the XML file
        self.indent(self.root)
        dump(self.root)

    def indent(self, elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def remove_bed(self, bed_string):
        ward_location = re.match(self.ward_regex, bed_string)
        return ward_location.groups()[0]

    def generate_spell_data(self, patient_id, patient, admit_offset):
        # Generate Spell data
        self.data.append(
            Comment('Spell data for patient {0}'.format(patient_id))
        )
        self.create_activity_spell_record(patient_id, patient,
                                          admit_offset)
        self.create_spell_record(patient_id, patient, admit_offset)
        self.update_activity_spell(patient_id)

    def generate_admit_movement_data(self, patient_id, patient, admit_offset):
        # Generate Admit Movement Data
        self.data.append(
            Comment('Admit movement for patient {0}'.format(patient_id))
        )
        self.create_activity_admit_movement_record(patient_id, patient,
                                                   admit_offset)
        self.create_admit_movement_record(patient_id, patient,
                                          admit_offset)
        self.update_activity_admit_movement(patient_id)

    def generate_adt_admit_data(self, patient_id, patient, admit_offset):
        # Generate ADT Admit data
        self.data.append(
            Comment('ADT Admit data for patient {0}'.format(patient_id))
        )
        self.create_activity_admit_record(patient_id, admit_offset)
        self.create_admit_record(patient_id, patient, admit_offset)
        self.update_activity_admit(patient_id)

    def generate_admission_data(self, patient_id, patient, admit_offset):
        # Generate Admission data
        self.data.append(
            Comment('Actual Admit data for patient {0}'.format(patient_id))
        )
        self.create_activity_admission_record(patient_id, patient,
                                              admit_offset)
        self.create_admission_record(patient_id, patient, admit_offset)
        self.update_activity_admission(patient_id)

    def generate_placement_data(self, patient_id, patient, admit_offset):
        self.data.append(
            Comment(
                'Placement data for patient {0}'.format(patient_id)
            )
        )
        self.create_activity_placement_record(patient_id, patient,
                                              admit_offset)
        self.create_placement_record(patient_id, patient)
        self.update_activity_placement(patient_id)

    def generate_placement_movement_data(self, patient_id, patient,
                                         admit_offset):
        # Generate Spell Movement Data
        self.data.append(
            Comment('Spell movement for patient {0}'.format(patient_id))
        )
        self.create_activity_placement_movement_record(patient_id, patient,
                                                       admit_offset)
        self.create_placement_movement_record(patient_id, patient,
                                              admit_offset)
        self.update_activity_placement_movement(patient_id)

    def admit_patients(self):
        """
        Read the patients in the document and admit them to the locations they
        are in
        :return:
        """
        for patient in self.demo_patients:
            patient_id_match = re.match(self.patient_id_regex,
                                        patient.attrib['id'])
            patient_id = patient_id_match.groups()[0]
            admit_offset = random.choice(self.admit_offset_list)

            self.generate_spell_data(patient_id, patient, admit_offset)
            self.generate_adt_admit_data(patient_id, patient, admit_offset)
            self.generate_admission_data(patient_id, patient, admit_offset)
            self.generate_admit_movement_data(patient_id, patient,
                                              admit_offset)

            # Generate placement data
            location_el = patient.find('field[@name=\'current_location_id\']')
            location = location_el.attrib['ref']
            if '_b' in location[-6:]:
                self.generate_placement_data(patient_id, patient, admit_offset)

    def create_activity_spell_record(self, patient_id, patient, admit_offset):
        # Create nh.activity ADT admission record with id
        activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.activity',
                'id': 'nhc_activity_demo_spell_{0}'.format(patient_id)
            }
        )

        state_field = SubElement(activity_admit_record, 'field',
                                 {'name': 'state'})
        state_field.text = 'started'

        # Create patient_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'patient_id',
                'ref': 'nhc_demo_patient_{0}'.format(patient_id)
            }
        )

        # Create activity data model
        activity_admit_model = SubElement(activity_admit_record,
                                          'field',
                                          {'name': 'data_model'})
        activity_admit_model.text = 'nh.clinical.spell'

        # Create parent_id reference
        location = patient.find('field[@name=\'current_location_id\']')\
            .attrib['ref']
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'location_id',
                'ref': location
            }
        )

        # Create activity date terminated
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'date_started',
                'eval': self.admit_date_eval_string.format(admit_offset)
            }
        )

    def create_spell_record(self, patient_id, patient, admit_offset):
        # Create nh.clinical.adt.patient.admit record with id & data
        activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.clinical.spell',
                'id': 'nhc_demo_spell_{0}'.format(patient_id)
            }
        )

        # Create activity_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'activity_id',
                'ref': 'nhc_activity_demo_spell_{0}'.format(patient_id)
            }
        )

        # Create patient_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'patient_id',
                'ref': 'nhc_demo_patient_{0}'.format(patient_id)
            }
        )

        # Create parent_id reference
        location = patient.find('field[@name=\'current_location_id\']')\
            .attrib['ref']
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'location_id',
                'ref': location
            }
        )

        # Create pos / hospital reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'pos_id',
                'ref': 'nhc_def_conf_pos_hospital'
            }
        )

        # Create code model
        admit_code = SubElement(activity_admit_record,
                                'field',
                                {'name': 'code'})
        admit_code.text = 'DEMO{0}'.format(patient_id.zfill(4))

        # Create activity date started
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'start_date',
                'eval': self.admit_date_eval_string.format(admit_offset)
            }
        )

    def update_activity_spell(self, patient_id):
        # Create nh.clinical.adt.patient.admit record with id & data
        update_activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.activity',
                'id': 'nhc_activity_demo_spell_{0}'.format(patient_id)
            }
        )

        # Create activity ref
        eval_string = '\'nh.clinical.spell,\' + ' \
                      'str(ref(\'nhc_demo_spell_{0}\'))'
        SubElement(
            update_activity_admit_record,
            'field',
            {
                'name': 'data_ref',
                'eval': eval_string.format(patient_id)
            }
        )

    def create_activity_admit_movement_record(self, patient_id, patient,
                                              admit_offset):
        activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.activity',
                'id': 'nhc_activity_demo_admit_move_{0}'.format(patient_id)
            }
        )

        # Create patient_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'patient_id',
                'ref': 'nhc_demo_patient_{0}'.format(patient_id)
            }
        )

        # Create creator_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'creator_id',
                'ref': 'nhc_activity_demo_admission_{0}'.format(patient_id)
            }
        )

        # Create parent_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'parent_id',
                'ref': 'nhc_activity_demo_spell_{0}'.format(patient_id)
            }
        )

        # Create spell_activity_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'spell_activity_id',
                'ref': 'nhc_activity_demo_spell_{0}'.format(patient_id)
            }
        )

        # Create state
        state_field = SubElement(activity_admit_record, 'field',
                                 {'name': 'state'})
        state_field.text = 'completed'

        # Create activity data model
        activity_admit_model = SubElement(activity_admit_record,
                                          'field',
                                          {'name': 'data_model'})
        activity_admit_model.text = 'nh.clinical.patient.move'

        # Create activity date terminated
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'date_started',
                'eval': self.admit_date_eval_string.format(admit_offset)
            }
        )

    def create_admit_movement_record(self, patient_id, patient, admit_offset):
        activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.clinical.patient.move',
                'id': 'nhc_demo_admit_move_{0}'.format(patient_id)
            }
        )

        # Create activity_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'activity_id',
                'ref': 'nhc_activity_demo_admit_move_{0}'.format(patient_id)
            }
        )

        # Create patient_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'patient_id',
                'ref': 'nhc_demo_patient_{0}'.format(patient_id)
            }
        )

        # Create parent_id reference
        location = patient.find('field[@name=\'current_location_id\']')\
            .attrib['ref']
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'location_id',
                'ref': self.remove_bed(location)
            }
        )

    def update_activity_admit_movement(self, patient_id):
        # Create nh.clinical.adt.patient.admit record with id & data
        update_activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.activity',
                'id': 'nhc_activity_demo_admit_move_{0}'.format(patient_id)
            }
        )

        # Create activity ref
        eval_string = '\'nh.clinical.patient.move,\' + ' \
                      'str(ref(\'nhc_demo_admit_move_{0}\'))'
        SubElement(
            update_activity_admit_record,
            'field',
            {
                'name': 'data_ref',
                'eval': eval_string.format(patient_id)
            }
        )

    def create_activity_admit_record(self, patient_id, admit_offset):
        # Create nh.activity ADT admit record with id
        activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.activity',
                'id': 'nhc_activity_demo_adt_admit_{0}'.format(patient_id)
            }
        )

        # Create patient_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'patient_id',
                'ref': 'nhc_demo_patient_{0}'.format(patient_id)
            }
        )

        # Create parent_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'parent_id',
                'ref': 'nhc_activity_demo_spell_{0}'.format(patient_id)
            }
        )

        # Create activity state
        activity_admit_state = SubElement(activity_admit_record,
                                          'field',
                                          {'name': 'state'})
        activity_admit_state.text = 'completed'

        # Create activity data model
        activity_admit_model = SubElement(activity_admit_record,
                                          'field',
                                          {'name': 'data_model'})
        activity_admit_model.text = 'nh.clinical.adt.patient.admit'

        # Create activity date terminated
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'date_terminated',
                'eval': self.admit_date_eval_string.format(admit_offset)
            }
        )

    def create_admit_record(self, patient_id, patient, admit_offset):
        # Create nh.clinical.adt.patient.admit record with id & data
        activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.clinical.adt.patient.admit',
                'id': 'nhc_demo_adt_admit_{0}'.format(patient_id)
            }
        )

        # Create activity_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'activity_id',
                'ref': 'nhc_activity_demo_adt_admit_{0}'.format(patient_id)
            }
        )

        # Create patient_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'patient_id',
                'ref': 'nhc_demo_patient_{0}'.format(patient_id)
            }
        )

        # Create parent_id reference
        location = patient.find('field[@name=\'current_location_id\']')\
            .attrib['ref']
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'location_id',
                'ref': self.remove_bed(location)
            }
        )

        # Create pos / hospital reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'pos_id',
                'ref': 'nhc_def_conf_pos_hospital'
            }
        )

        # Create location state
        admit_location = SubElement(activity_admit_record,
                                    'field',
                                    {'name': 'location'})
        admit_location.text = 'A'

        # Create code model
        admit_code = SubElement(activity_admit_record,
                                'field',
                                {'name': 'code'})
        admit_code.text = 'DEMO{0}'.format(patient_id.zfill(4))

        # Create activity date started
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'start_date',
                'eval': self.admit_date_eval_string.format(admit_offset)
            }
        )

        # Create patient ID
        patient_identifier = patient\
            .find('field[@name=\'patient_identifier\']').text
        patient_id_field = SubElement(activity_admit_record, 'field',
                                      {'name': 'patient_identifier'})
        patient_id_field.text = patient_identifier

        # Create Other ID
        other_identifier = patient\
            .find('field[@name=\'other_identifier\']').text
        other_id_field = SubElement(activity_admit_record, 'field',
                                    {'name': 'other_identifier'})
        other_id_field.text = other_identifier

    def update_activity_admit(self, patient_id):
        # Create nh.clinical.adt.patient.admit record with id & data
        update_activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.activity',
                'id': 'nhc_activity_demo_adt_admit_{0}'.format(patient_id)
            }
        )

        # Create activity ref
        eval_string = '\'nh.clinical.adt.patient.admit,\' + ' \
                      'str(ref(\'nhc_demo_adt_admit_{0}\'))'
        SubElement(
            update_activity_admit_record,
            'field',
            {
                'name': 'data_ref',
                'eval': eval_string.format(patient_id)
            }
        )

    def create_activity_admission_record(self, patient_id, patient,
                                         admit_offset):
        # Create nh.activity ADT admission record with id
        activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.activity',
                'id': 'nhc_activity_demo_admission_{0}'.format(patient_id)
            }
        )

        # Create patient_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'patient_id',
                'ref': 'nhc_demo_patient_{0}'.format(patient_id)
            }
        )

        # Create creator_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'creator_id',
                'ref': 'nhc_activity_demo_adt_admit_{0}'.format(patient_id)
            }
        )

        # Create parent_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'parent_id',
                'ref': 'nhc_activity_demo_spell_{0}'.format(patient_id)
            }
        )

        # Create spell_activity_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'spell_activity_id',
                'ref': 'nhc_activity_demo_spell_{0}'.format(patient_id)
            }
        )

        # Create activity state
        activity_admit_state = SubElement(activity_admit_record,
                                          'field',
                                          {'name': 'state'})
        activity_admit_state.text = 'completed'

        # Create activity data model
        activity_admit_model = SubElement(activity_admit_record,
                                          'field',
                                          {'name': 'data_model'})
        activity_admit_model.text = 'nh.clinical.patient.admission'

        # Create parent_id reference
        location = patient.find('field[@name=\'current_location_id\']')\
            .attrib['ref']
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'location_id',
                'ref': self.remove_bed(location)
            }
        )

        # Create activity date terminated
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'date_terminated',
                'eval': self.admit_date_eval_string.format(admit_offset)
            }
        )

    def create_admission_record(self, patient_id, patient, admit_offset):
        # Create nh.clinical.adt.patient.admit record with id & data
        activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.clinical.patient.admission',
                'id': 'nhc_demo_admission_{0}'.format(patient_id)
            }
        )

        # Create activity_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'activity_id',
                'ref': 'nhc_activity_demo_admission_{0}'.format(patient_id)
            }
        )

        # Create patient_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'patient_id',
                'ref': 'nhc_demo_patient_{0}'.format(patient_id)
            }
        )

        # Create parent_id reference
        location = patient.find('field[@name=\'current_location_id\']')\
            .attrib['ref']
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'location_id',
                'ref': self.remove_bed(location)
            }
        )

        # Create pos / hospital reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'pos_id',
                'ref': 'nhc_def_conf_pos_hospital'
            }
        )

        # Create code model
        admit_code = SubElement(activity_admit_record,
                                'field',
                                {'name': 'code'})
        admit_code.text = 'DEMO{0}'.format(patient_id.zfill(4))

        # Create activity date started
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'start_date',
                'eval': self.admit_date_eval_string.format(admit_offset)
            }
        )

    def update_activity_admission(self, patient_id):
        # Create nh.clinical.adt.patient.admit record with id & data
        update_activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.activity',
                'id': 'nhc_activity_demo_admission_{0}'.format(patient_id)
            }
        )

        # Create activity ref
        eval_string = '\'nh.clinical.patient.admission,\' + ' \
                      'str(ref(\'nhc_demo_admission_{0}\'))'
        SubElement(
            update_activity_admit_record,
            'field',
            {
                'name': 'data_ref',
                'eval': eval_string.format(patient_id)
            }
        )

    def create_activity_placement_record(self, patient_id, patient,
                                         admit_offset):
        # Create nh.activity ADT admission record with id
        activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.activity',
                'id': 'nhc_activity_demo_placement_{0}'.format(patient_id)
            }
        )

        # Create patient_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'patient_id',
                'ref': 'nhc_demo_patient_{0}'.format(patient_id)
            }
        )

        # Create creator_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'creator_id',
                'ref': 'nhc_activity_demo_admission_{0}'.format(patient_id)
            }
        )

        # Create parent_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'parent_id',
                'ref': 'nhc_activity_demo_spell_{0}'.format(patient_id)
            }
        )

        # Create spell_activity_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'spell_activity_id',
                'ref': 'nhc_activity_demo_spell_{0}'.format(patient_id)
            }
        )

        # Create activity state
        activity_admit_state = SubElement(activity_admit_record,
                                          'field',
                                          {'name': 'state'})
        activity_admit_state.text = 'completed'

        # Create activity data model
        activity_admit_model = SubElement(activity_admit_record,
                                          'field',
                                          {'name': 'data_model'})
        activity_admit_model.text = 'nh.clinical.patient.placement'

        # Create parent_id reference
        location = patient.find('field[@name=\'current_location_id\']')\
            .attrib['ref']
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'location_id',
                'ref': self.remove_bed(location)
            }
        )

        # Create activity date terminated
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'date_terminated',
                'eval': self.admit_date_eval_string.format(admit_offset)
            }
        )

    def create_placement_record(self, patient_id, patient):
        # Create nh.clinical.adt.patient.admit record with id & data
        activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.clinical.patient.placement',
                'id': 'nhc_demo_placement_{0}'.format(patient_id)
            }
        )

        # Create activity_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'activity_id',
                'ref': 'nhc_activity_demo_placement_{0}'.format(patient_id)
            }
        )

        # Create patient_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'patient_id',
                'ref': 'nhc_demo_patient_{0}'.format(patient_id)
            }
        )

        # Create parent_id reference
        location = patient.find('field[@name=\'current_location_id\']')\
            .attrib['ref']
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'suggested_location_id',
                'ref': self.remove_bed(location)
            }
        )

        # Create pos / hospital reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'location_id',
                'ref': location
            }
        )

    def update_activity_placement(self, patient_id):
        # Create nh.clinical.adt.patient.admit record with id & data
        update_activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.activity',
                'id': 'nhc_activity_demo_placement_{0}'.format(patient_id)
            }
        )

        # Create activity ref
        eval_string = '\'nh.clinical.patient.placement,\' + ' \
                      'str(ref(\'nhc_demo_placement_{0}\'))'
        SubElement(
            update_activity_admit_record,
            'field',
            {
                'name': 'data_ref',
                'eval': eval_string.format(patient_id)
            }
        )

    def create_activity_placement_movement_record(self, patient_id, patient,
                                                  admit_offset):
        activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.activity',
                'id': 'nhc_activity_demo_placement_move_{0}'.format(patient_id)
            }
        )

        # Create patient_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'patient_id',
                'ref': 'nhc_demo_patient_{0}'.format(patient_id)
            }
        )

        # Create creator_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'creator_id',
                'ref': 'nhc_activity_demo_placement_{0}'.format(patient_id)
            }
        )

        # Create parent_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'parent_id',
                'ref': 'nhc_activity_demo_spell_{0}'.format(patient_id)
            }
        )

        # Create spell_activity_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'spell_activity_id',
                'ref': 'nhc_activity_demo_spell_{0}'.format(patient_id)
            }
        )

        # Create state
        state_field = SubElement(activity_admit_record, 'field',
                                 {'name': 'state'})
        state_field.text = 'completed'

        # Create activity data model
        activity_admit_model = SubElement(activity_admit_record,
                                          'field',
                                          {'name': 'data_model'})
        activity_admit_model.text = 'nh.clinical.patient.move'

        # Create parent_id reference
        location = patient.find('field[@name=\'current_location_id\']')\
            .attrib['ref']
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'location_id',
                'ref': self.remove_bed(location)
            }
        )

        # Create activity date terminated
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'date_started',
                'eval': self.admit_date_eval_string.format(admit_offset)
            }
        )

    def create_placement_movement_record(self, patient_id, patient,
                                         admit_offset):
        activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.clinical.patient.move',
                'id': 'nhc_demo_placement_move_{0}'.format(patient_id)
            }
        )

        # Create activity_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'activity_id',
                'ref': 'nhc_activity_demo_placement_move_{0}'.format(
                        patient_id)
            }
        )

        # Create patient_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'patient_id',
                'ref': 'nhc_demo_patient_{0}'.format(patient_id)
            }
        )

        # Create parent_id reference
        location = patient.find('field[@name=\'current_location_id\']')\
            .attrib['ref']
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'from_location_id',
                'ref': self.remove_bed(location)
            }
        )
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'location_id',
                'ref': location
            }
        )

    def update_activity_placement_movement(self, patient_id):
        # Create nh.clinical.adt.patient.admit record with id & data
        update_activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.activity',
                'id': 'nhc_activity_demo_placement_move_{0}'.format(patient_id)
            }
        )

        # Create activity ref
        eval_string = '\'nh.clinical.patient.move,\' + ' \
                      'str(ref(\'nhc_demo_placement_move_{0}\'))'
        SubElement(
            update_activity_admit_record,
            'field',
            {
                'name': 'data_ref',
                'eval': eval_string.format(patient_id)
            }
        )


wards = ['a']
for ward in wards:
    OperationsGenerator(ward)
