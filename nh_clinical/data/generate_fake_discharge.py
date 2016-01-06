from xml.etree.ElementTree import Element, SubElement, Comment, dump, parse
import random
import re


class DischargeGenerator(object):

    def __init__(self, ward_file, counter_offset, total_to_discharge):

        # Create root element
        self.root = Element('openerp')

        # Create data inside root element
        self.data = SubElement(self.root, 'data', {'noupdate': '1'})

        # Read the patient XML file
        patient_data = parse('ward_{0}/demo_patients.xml'.format(ward_file))
        self.demo_patients = patient_data.findall('data')[0].findall('record')

        # Regex to use to get the ID for a patient from id attribute on record
        patient_id_regex_string = 'nhc_demo_patient_(\d+)'
        self.patient_id_regex = re.compile(patient_id_regex_string)
        self.discharge_date_eval_string = '(datetime.now())' \
                                          '.strftime(\'%Y-%m-%d 00:00:00\')'

        # Generate the patient admissions
        self.discharge_patients(counter_offset, total_to_discharge)

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

    def generate_discharge_data(self, patient_id, patient, location):
        # Generate Admission data
        self.data.append(
            Comment('ADT Discharge data for patient {0}'.format(patient_id))
        )
        self.create_activity_adt_discharge_record(patient_id, patient)
        self.create_adt_discharge_record(patient_id, patient, location)
        self.update_activity_adt_discharge(patient_id)

    def generate_discharge_operation_data(self, patient_id, patient, location):
        self.data.append(
            Comment(
                'Actual Discharge for patient {0}'.format(patient_id)
            )
        )
        self.create_activity_discharge_record(patient_id, patient, location)
        self.create_discharge_record(patient_id, patient, location)
        self.update_activity_discharge(patient_id)

    def generate_spell_close_data(self, patient_id, patient, location):
        # Generate Spell Movement Data
        self.data.append(
            Comment('Spell closure for patient {0}'.format(patient_id))
        )
        self.create_activity_spell_close_record(patient_id, patient, location)
        self.create_spell_close_record(patient_id, patient, location)
        self.update_activity_spell_close(patient_id)

    def discharge_patients(self, counter_offset, total_to_discharge):
        """
        Read the patients in the document and admit them to the locations they
        are in
        :param counter_offset: The offset for the counter if using with another
        tool
        :param total_to_discharge: The number of patients to discharge
        :return:
        """
        counter = 0 + counter_offset
        for patient in self.demo_patients:
            patient_id_match = re.match(self.patient_id_regex,
                                        patient.attrib['id'])
            patient_id = patient_id_match.groups()[0]

            location_el = patient.find('field[@name=\'current_location_id\']')
            location = location_el.attrib['ref']
            if '_b' not in location[-6:]:
                if counter < total_to_discharge:
                    self.generate_discharge_data(patient_id, patient, location)
                    self.generate_discharge_operation_data(patient_id, patient,
                                                           location)
                    self.generate_spell_close_data(patient_id, patient,
                                                   location)
                    counter += 1

    def create_activity_adt_discharge_record(self, patient_id, patient):
        # Create nh.activity ADT admission record with id
        activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.activity',
                'id': 'nhc_activity_demo_adt_discharge_{0}'.format(patient_id)
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

        # Create spell id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'parent_id',
                'ref': 'nhc_activity_demo_spell_{0}'.format(patient_id)
            }
        )
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'spell_activity_id',
                'ref': 'nhc_activity_demo_spell_{0}'.format(patient_id)
            }
        )


        state_field = SubElement(activity_admit_record, 'field',
                                 {'name': 'state'})
        state_field.text = 'completed'

        # Create activity data model
        activity_admit_model = SubElement(activity_admit_record,
                                          'field',
                                          {'name': 'data_model'})
        activity_admit_model.text = 'nh.clinical.adt.patient.discharge'

        # Create activity date terminated
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'date_terminated',
                'eval': self.discharge_date_eval_string
            }
        )

    def create_adt_discharge_record(self, patient_id, patient, location):
        # Create nh.clinical.adt.patient.admit record with id & data
        activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.clinical.adt.patient.discharge',
                'id': 'nhc_demo_adt_discharge_{0}'.format(patient_id)
            }
        )

        # Create activity_id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'activity_id',
                'ref': 'nhc_activity_demo_adt_discharge_{0}'.format(patient_id)
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
                'name': 'location_id',
                'ref': location
            }
        )

        # Create pos / hospital reference
        discharge_location = SubElement(activity_admit_record,
                                        'field',
                                        {'name': 'location'})
        discharge_location.text = 'A'

        # patient identifier model
        patient_ident = patient.find('field[@name=\'patient_identifier\']')\
            .text
        patient_ident_field = SubElement(activity_admit_record,
                                         'field',
                                         {'name': 'patient_identifier'})
        patient_ident_field.text = patient_ident
        
        # other identifier model
        other_ident = patient.find('field[@name=\'other_identifier\']')\
            .text
        other_ident_field = SubElement(activity_admit_record,
                                       'field',
                                       {'name': 'other_identifier'})
        other_ident_field.text = other_ident

        # Create activity date started
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'discharge_date',
                'eval': self.discharge_date_eval_string
            }
        )

    def update_activity_adt_discharge(self, patient_id):
        # Create nh.clinical.adt.patient.admit record with id & data
        update_activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.activity',
                'id': 'nhc_activity_demo_adt_discharge_{0}'.format(patient_id)
            }
        )

        # Create activity ref
        eval_string = '\'nh.clinical.adt.patient.discharge,\' + ' \
                      'str(ref(\'nhc_demo_adt_discharge_{0}\'))'
        SubElement(
            update_activity_admit_record,
            'field',
            {
                'name': 'data_ref',
                'eval': eval_string.format(patient_id)
            }
        )

    def create_activity_discharge_record(self, patient_id, patient, location):
        # Create nh.activity ADT admission record with id
        activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.activity',
                'id': 'nhc_activity_demo_discharge_{0}'.format(patient_id)
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

        # Create ADT Discharge id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'creator_id',
                'ref': 'nhc_activity_demo_adt_discharge_{0}'.format(patient_id)
            }
        )

        # Create spell id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'parent_id',
                'ref': 'nhc_activity_demo_spell_{0}'.format(patient_id)
            }
        )

        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'spell_activity_id',
                'ref': 'nhc_activity_demo_spell_{0}'.format(patient_id)
            }
        )

        state_field = SubElement(activity_admit_record, 'field',
                                 {'name': 'state'})
        state_field.text = 'completed'

        # Create activity data model
        activity_admit_model = SubElement(activity_admit_record,
                                          'field',
                                          {'name': 'data_model'})
        activity_admit_model.text = 'nh.clinical.patient.discharge'

        # Create activity date terminated
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
                'name': 'discharge_date',
                'eval': self.discharge_date_eval_string
            }
        )

    def create_discharge_record(self, patient_id, patient, location):
        # Create nh.activity ADT admission record with id
        activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.clinical.patient.discharge',
                'id': 'nhc_demo_discharge_{0}'.format(patient_id)
            }
        )

        # Create activity id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'activity_id',
                'ref': 'nhc_activity_demo_discharge_{0}'.format(patient_id)
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

        # Create ADT Discharge id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'location_id',
                'ref': location
            }
        )

        # Create spell id reference
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'pos_id',
                'ref': 'nhc_def_conf_pos_hospital'
            }
        )

        state_field = SubElement(activity_admit_record, 'field',
                                 {'name': 'code'})
        state_field.text = 'DEMO{0}'.format(patient_id.zfill(4))

        # Create activity date terminated
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'date_terminated',
                'eval': self.discharge_date_eval_string
            }
        )

    def update_activity_discharge(self, patient_id):
        # Create nh.clinical.adt.patient.admit record with id & data
        update_activity_admit_record = SubElement(
            self.data,
            'record',
            {
                'model': 'nh.activity',
                'id': 'nhc_activity_demo_discharge_{0}'.format(patient_id)
            }
        )

        # Create activity ref
        eval_string = '\'nh.clinical.patient.discharge,\' + ' \
                      'str(ref(\'nhc_demo_discharge_{0}\'))'
        SubElement(
            update_activity_admit_record,
            'field',
            {
                'name': 'data_ref',
                'eval': eval_string.format(patient_id)
            }
        )

    def create_activity_spell_close_record(self, patient_id, patient,
                                           location):
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
        state_field.text = 'completed'

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

        # Create location
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
                'name': 'date_terminated',
                'eval': self.discharge_date_eval_string
            }
        )

    def create_spell_close_record(self, patient_id, patient, location):
        # Create nh.activity ADT admission record with id
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

        # Create location
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'location_id',
                'ref': location
            }
        )

        # Create pos
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'pos_id',
                'ref': 'nhc_def_conf_pos_hospital'
            }
        )

        state_field = SubElement(activity_admit_record, 'field',
                                 {'name': 'code'})
        state_field.text = 'DEMO{0}'.format(patient_id.zfill(4))

        # Create activity date terminated
        SubElement(
            activity_admit_record,
            'field',
            {
                'name': 'date_terminated',
                'eval': self.discharge_date_eval_string
            }
        )

    def update_activity_spell_close(self, patient_id):
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


wards = ['a', 'b', 'c', 'd', 'e']
for ward in wards:
    DischargeGenerator(ward, 0, 4)
