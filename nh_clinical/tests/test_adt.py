from datetime import datetime as dt
import logging

from openerp.tests import common
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as dtf

_logger = logging.getLogger(__name__)

from faker import Faker
fake = Faker()
seed = fake.random_int(min=0, max=9999999)


def next_seed():
    global seed
    seed += 1
    return seed


class test_adt(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(test_adt, cls).setUpClass()
        cr, uid = cls.cr, cls.uid

        cls.users_pool = cls.registry('res.users')
        cls.groups_pool = cls.registry('res.groups')
        cls.partner_pool = cls.registry('res.partner')
        cls.activity_pool = cls.registry('nh.activity')
        cls.patient_pool = cls.registry('nh.clinical.patient')
        cls.location_pool = cls.registry('nh.clinical.location')
        cls.pos_pool = cls.registry('nh.clinical.pos')
        cls.admission_pool = cls.registry('nh.clinical.patient.admission')
        cls.spell_pool = cls.registry('nh.clinical.spell')
        # ADT DATA MODELS
        cls.register_pool = cls.registry('nh.clinical.adt.patient.register')
        cls.admit_pool = cls.registry('nh.clinical.adt.patient.admit')
        cls.cancel_admit_pool = cls.registry('nh.clinical.adt.patient.cancel_admit')
        cls.transfer_pool = cls.registry('nh.clinical.adt.patient.transfer')
        cls.cancel_transfer_pool = cls.registry('nh.clinical.adt.patient.cancel_transfer')
        cls.discharge_pool = cls.registry('nh.clinical.adt.patient.discharge')
        cls.cancel_discharge_pool = cls.registry('nh.clinical.adt.patient.cancel_discharge')
        cls.merge_pool = cls.registry('nh.clinical.adt.patient.merge')
        cls.update_pool = cls.registry('nh.clinical.adt.patient.update')
        cls.spell_update_pool = cls.registry('nh.clinical.adt.spell.update')
        
        cls.apidemo = cls.registry('nh.clinical.api.demo')

        cls.patient_ids = cls.apidemo.build_unit_test_env1(cr, uid)

        cls.wu_id = cls.location_pool.search(cr, uid, [('code', '=', 'U')])[0]
        cls.wt_id = cls.location_pool.search(cr, uid, [('code', '=', 'T')])[0]
        cls.pos_id = cls.location_pool.read(cr, uid, cls.wu_id, ['pos_id'])['pos_id'][0]
        cls.pos_location_id = cls.pos_pool.read(cr, uid, cls.pos_id, ['location_id'])['location_id'][0]

        cls.wmu_id = cls.users_pool.search(cr, uid, [('login', '=', 'WMU')])[0]
        cls.wmt_id = cls.users_pool.search(cr, uid, [('login', '=', 'WMT')])[0]
        cls.nu_id = cls.users_pool.search(cr, uid, [('login', '=', 'NU')])[0]
        cls.nt_id = cls.users_pool.search(cr, uid, [('login', '=', 'NT')])[0]
        cls.adt_id = cls.users_pool.search(cr, uid, [('groups_id.name', 'in', ['NH Clinical ADT Group']), ('pos_id', '=', cls.pos_id)])[0]
    #
    # def test_adt_patient_register(self):
    #     cr, uid = self.cr, self.uid
    #


    def test_adt_Register_and_PatientUpdate(self):
        cr, uid = self.cr, self.uid

        fake.seed(next_seed())
        gender = fake.random_element(('M', 'F'))
        other_identifier = str(fake.random_int(min=1000001, max=9999999))
        dob = fake.date_time_between(start_date="-80y", end_date="-10y").strftime("%Y-%m-%d %H:%M:%S")
        family_name = fake.last_name()
        given_name = fake.first_name()

        register_data = {
            'family_name': family_name,
            'given_name': given_name,
            'other_identifier': other_identifier,
            'dob': dob,
            'gender': gender,
            'sex': gender}

        register_activity_id = self.register_pool.create_activity(cr, self.adt_id, {}, {})
        self.activity_pool.submit(cr, self.adt_id, register_activity_id, register_data)
        check_register = self.activity_pool.browse(cr, self.adt_id, register_activity_id)

        # test register activity data
        self.assertTrue(check_register.data_ref.family_name == family_name, msg="Patient Register: Family name was not submitted correctly")
        self.assertTrue(check_register.data_ref.given_name == given_name, msg="Patient Register: Given name was not submitted correctly")
        self.assertTrue(check_register.data_ref.other_identifier == other_identifier, msg="Patient Register: Hospital number was not submitted correctly")
        self.assertTrue(check_register.data_ref.dob == dob, msg="Patient Register: Date of birth was not submitted correctly")
        self.assertTrue(check_register.data_ref.gender == gender, msg="Patient Register: Gender was not submitted correctly")
        self.assertTrue(check_register.data_ref.sex == gender, msg="Patient Register: Sex was not submitted correctly")
        self.assertTrue(check_register.data_ref.pos_id.id == self.pos_id, msg="Patient Register: Point of Service was not submitted correctly")
        self.assertFalse(check_register.data_ref.middle_names, msg="Patient Register: Middle name was not submitted correctly")
        self.assertFalse(check_register.data_ref.patient_identifier, msg="Patient Register: NHS number was not submitted correctly")
        self.assertFalse(check_register.data_ref.title, msg="Patient Register: Title was not submitted correctly")
        
        # Complete Patient Register
        self.activity_pool.complete(cr, self.adt_id, register_activity_id)
        check_register = self.activity_pool.browse(cr, uid, register_activity_id)
        self.assertTrue(check_register.state == 'completed', msg="Patient Register not completed successfully")
        self.assertTrue(check_register.date_terminated, msg="Patient Register Completed: Date terminated not registered")
        # test patient data
        patient_id = self.patient_pool.search(cr, uid, [['other_identifier', '=', other_identifier]])
        self.assertTrue(patient_id, msg="Patient Register: Patient not created successfully")
        self.assertTrue(check_register.data_ref.patient_id.id == patient_id[0], msg="Patient Register: Patient was not registered correctly")
        check_patient = self.patient_pool.browse(cr, uid, patient_id[0])
        self.assertTrue(check_patient.family_name == family_name, msg="Patient Register Completed: Family name is not correct")
        self.assertTrue(check_patient.given_name == given_name, msg="Patient Register Completed: Given name is not correct")
        self.assertTrue(check_patient.other_identifier == other_identifier, msg="Patient Register Completed: Hospital number is not correct")
        self.assertTrue(check_patient.dob == dob, msg="Patient Register Completed: Date of birth is not correct")
        self.assertTrue(check_patient.gender == gender, msg="Patient Register Completed: Gender is not correct")
        self.assertTrue(check_patient.sex == gender, msg="Patient Register Completed: Sex is not correct")
        self.assertFalse(check_patient.middle_names, msg="Patient Register Completed: Middle name is not correct")
        self.assertFalse(check_patient.patient_identifier, msg="Patient Register Completed: NHS number is not correct")
        self.assertFalse(check_patient.title, msg="Patient Register Completed: Title is not correct")

        # Patient Update
        update_data = {
            'family_name': fake.last_name(),
            'given_name': fake.first_name(),
            'other_identifier': other_identifier,
            'dob': fake.date_time_between(start_date="-80y", end_date="-10y").strftime("%Y-%m-%d %H:%M:%S"),
            'gender': gender,
            'sex': gender}
        update_activity_id = self.update_pool.create_activity(cr, self.adt_id, {}, {})
        self.activity_pool.submit(cr, self.adt_id, update_activity_id, update_data)
        check_update = self.activity_pool.browse(cr, self.adt_id, update_activity_id)

        # test Patient Update activity data
        self.assertTrue(check_update.data_ref.family_name == update_data['family_name'], msg="Patient Update: Family name was not submitted correctly")
        self.assertTrue(check_update.data_ref.given_name == update_data['given_name'], msg="Patient Update: Given name was not submitted correctly")
        self.assertTrue(check_update.data_ref.other_identifier == other_identifier, msg="Patient Update: Hospital number was not submitted correctly")
        self.assertTrue(check_update.data_ref.dob == update_data['dob'], msg="Patient Update: Date of birth was not submitted correctly")
        self.assertTrue(check_update.data_ref.gender == gender, msg="Patient Update: Gender was not submitted correctly")
        self.assertTrue(check_update.data_ref.sex == gender, msg="Patient Update: Sex was not submitted correctly")
        self.assertTrue(check_update.data_ref.patient_id.id == patient_id[0], msg="Patient Update: Patient id was not registered correctly")
        self.assertFalse(check_update.data_ref.middle_names, msg="Patient Update: Middle name was not submitted correctly")
        self.assertFalse(check_update.data_ref.patient_identifier, msg="Patient Update: NHS number was not submitted correctly")
        self.assertFalse(check_update.data_ref.title, msg="Patient Update: Title was not registered correctly")
        # Complete Patient Update
        self.activity_pool.complete(cr, self.adt_id, update_activity_id)
        check_update = self.activity_pool.browse(cr, uid, update_activity_id)
        self.assertTrue(check_update.state == 'completed', msg="Patient Update not completed successfully")
        self.assertTrue(check_update.date_terminated, msg="Patient Update Completed: Date terminated not registered")
        # test patient data
        check_patient = self.patient_pool.browse(cr, uid, patient_id[0])
        self.assertTrue(check_patient.family_name == update_data['family_name'], msg="Patient Update Completed: Family name is not correct")
        self.assertTrue(check_patient.given_name == update_data['given_name'], msg="Patient Update Completed: Given name is not correct")
        self.assertTrue(check_patient.other_identifier == other_identifier, msg="Patient Update Completed: Hospital number is not correct")
        self.assertTrue(check_patient.dob == update_data['dob'], msg="Patient Update Completed: Date of birth is not correct")
        self.assertTrue(check_patient.gender == gender, msg="Patient Update Completed: Gender is not correct")
        self.assertTrue(check_patient.sex == gender, msg="Patient Update Completed: Sex is not correct")
        self.assertFalse(check_patient.middle_names, msg="Patient Update Completed: Middle name is not correct")
        self.assertFalse(check_patient.patient_identifier, msg="Patient Update Completed: NHS number is not correct")
        self.assertFalse(check_patient.title, msg="Patient Update Completed: Title is not correct")

        # Register patient with wrong user test
        # try:
        #     register_activity_id = self.register_pool.create_activity(cr, self.adt_id, {}, {})
        #     self.activity_pool.submit(cr, uid, register_activity_id, register_data)
        # except Exception as e:
        #     self.assertTrue(e.args[1].startswith("POS location is not set for user"), msg="Unexpected reaction to attempt to register with wrong user!")
        # else:
        #     assert False, "Unexpected reaction to attempt to register with wrong user!"

        # Register patient without Hospital number/NHS number
        try:
            register_activity_id = self.register_pool.create_activity(cr, self.adt_id, {}, {})
            self.activity_pool.submit(cr, self.adt_id, register_activity_id, {})
        except Exception as e:
            self.assertTrue(e.args[1].startswith("patient_identifier or other_identifier not found in submitted data!"), msg="Unexpected reaction to attempt to register without required data!")
        else:
            assert False, "Unexpected reaction to attempt to register without required data!"

        # Register existing patient
        try:
            register_activity_id = self.register_pool.create_activity(cr, self.adt_id, {}, {})
            self.activity_pool.submit(cr, self.adt_id, register_activity_id, register_data)
        except Exception as e:
            self.assertTrue(e.args[1].startswith("Patient already exists!"), msg="Unexpected reaction to attempt to register an existing patient!")
        else:
            assert False, "Unexpected reaction to attempt to register an existing patient!"
        
    def test_adt_Admit_SpellUpdate_Transfer_CancelTransfer_Discharge_CancelDischarge_and_CancelAdmit(self):
        cr, uid = self.cr, self.uid
        # edge cases MISSING (try/except)
        fake.seed(next_seed())        
        patient_id = fake.random_element(self.patient_ids)
        other_identifier = self.patient_pool.browse(cr, uid, patient_id).other_identifier
        code = str(fake.random_int(min=1000001, max=9999999))
        start_date = dt.now().strftime(dtf)
        doctors = [{
            'type': 'c', 
            'code': 'C1', 
            'title': 'Dr', 
            'given_name': fake.first_name(), 
            'family_name': fake.last_name()
        }, {
            'type': 'r', 
            'code': 'R1', 
            'title': 'Dr', 
            'given_name': fake.first_name(), 
            'family_name': fake.last_name()
        }]        
                
        admit_data = {
            'other_identifier': other_identifier,
            'location': 'U',
            'code': code,
            'start_date': start_date, 
            'doctors': doctors}
        
        admit_activity_id = self.admit_pool.create_activity(cr, self.adt_id, {}, {})
        self.activity_pool.submit(cr, self.adt_id, admit_activity_id, admit_data)
        check_admit = self.activity_pool.browse(cr, self.adt_id, admit_activity_id)
        
        # test admit activity submitted data
        self.assertTrue(check_admit.data_ref.other_identifier == other_identifier, msg="Patient Admit: Hospital number was not submitted correctly")
        self.assertTrue(check_admit.data_ref.location == 'U', msg="Patient Admit: Location was not submitted correctly")
        self.assertTrue(check_admit.data_ref.code == code, msg="Patient Admit: Visit code was not submitted correctly")
        self.assertTrue(check_admit.data_ref.start_date == start_date, msg="Patient Admit: Admission date was not submitted correctly")
        self.assertTrue(eval(check_admit.data_ref.doctors) == doctors, msg="Patient Admit: Doctors information was not submitted correctly")
        # test admit activity computed data
        self.assertTrue(check_admit.data_ref.suggested_location_id.id == self.wu_id, msg="Patient Admit: Location id not registered correctly")
        self.assertTrue(check_admit.data_ref.pos_id.id == self.pos_id, msg="Patient Admit: Point of Service was not registered correctly")
        self.assertTrue(check_admit.data_ref.patient_id.id == patient_id, msg="Patient Admit: Patient id was not registered correctly")        
        ref_doctors = [refd for refd in check_admit.data_ref.ref_doctor_ids]
        con_doctors = [cond for cond in check_admit.data_ref.con_doctor_ids]
        self.assertTrue(len(ref_doctors) == 1, msg="Patient Admit: Ref Doctors not registered correctly")
        self.assertTrue(len(con_doctors) == 1, msg="Patient Admit: Consultant Doctors not registered correctly")
        self.assertTrue(ref_doctors[0].name == "%s, %s" % (doctors[1]['family_name'], doctors[1]['given_name']), msg="Patient Admit: Ref Doctors data not registered correctly")
        self.assertTrue(con_doctors[0].name == "%s, %s" % (doctors[0]['family_name'], doctors[0]['given_name']), msg="Patient Admit: Consultant Doctors data not registered correctly")
        admit_ref_doctor = ref_doctors[0].id
        admit_con_doctor = con_doctors[0].id

        # Complete Patient Admit
        self.activity_pool.complete(cr, self.adt_id, admit_activity_id)
        check_admit = self.activity_pool.browse(cr, uid, admit_activity_id)
        self.assertTrue(check_admit.state == 'completed', msg="Patient Admit not completed successfully")
        self.assertTrue(check_admit.date_terminated, msg="Patient Admit Completed: Date terminated not registered")
        # test admission and spell data
        admission_id = self.admission_pool.search(cr, uid, [['code', '=', code]])
        self.assertTrue(admission_id, msg="Patient Admit: Admission not created successfully")
        spell_id = self.spell_pool.search(cr, uid, [['code', '=', code]])
        self.assertTrue(spell_id, msg="Patient Admit: Spell not created successfully")
        check_spell = self.spell_pool.browse(cr, uid, spell_id[0])
        self.assertTrue(check_admit.parent_id.id == check_spell.activity_id.id, msg="Patient Admit: Spell was not registered correctly")
        self.assertTrue(check_spell.patient_id.id == patient_id, msg= "Patient Admit Completed: Spell patient not registered correctly")
        self.assertTrue(check_spell.pos_id.id == self.pos_id, msg= "Patient Admit Completed: Spell point of service not registered correctly")
        self.assertTrue(check_spell.code == code, msg= "Patient Admit Completed: Spell code not registered correctly")
        self.assertTrue(check_spell.start_date == start_date, msg= "Patient Admit Completed: Spell start date not registered correctly")
        self.assertTrue(check_spell.activity_id.state == 'started', msg= "Patient Admit Completed: Spell state incorrect")
        ref_doctors = [refd.id for refd in check_spell.ref_doctor_ids]
        con_doctors = [cond.id for cond in check_spell.con_doctor_ids]
        self.assertTrue(len(ref_doctors) == 1, msg="Patient Admit Completed: Spell Ref Doctors not registered correctly")
        self.assertTrue(len(con_doctors) == 1, msg="Patient Admit Completed: Spell Consultant Doctors not registered correctly")
        self.assertTrue(ref_doctors[0] == admit_ref_doctor, msg="Patient Admit Completed: Spell Ref Doctors not registered correctly")
        self.assertTrue(con_doctors[0] == admit_con_doctor, msg="Patient Admit Completed: Spell Consultant Doctors not registered correctly")

        # Spell Update
        update_doctors = [{
            'type': 'c',
            'code': 'C2',
            'title': 'Dr',
            'given_name': fake.first_name(),
            'family_name': fake.last_name()
        }, {
            'type': 'r',
            'code': 'R2',
            'title': 'Dr',
            'given_name': fake.first_name(),
            'family_name': fake.last_name()
        }]

        update_data = {
            'other_identifier': other_identifier,
            'location': 'T',
            'doctors': update_doctors}

        update_activity_id = self.spell_update_pool.create_activity(cr, self.adt_id, {}, {})
        self.activity_pool.submit(cr, self.adt_id, update_activity_id, update_data)
        check_update = self.activity_pool.browse(cr, self.adt_id, update_activity_id)
        # test Spell Update activity data
        self.assertTrue(check_update.data_ref.other_identifier == other_identifier, msg="Spell Update: Hospital number not submitted correctly")
        self.assertTrue(check_update.data_ref.location == 'T', msg="Spell Update: Location was not submitted correctly")
        self.assertTrue(eval(check_update.data_ref.doctors) == update_doctors, msg="Spell Update: Doctors was not submitted correctly")
        self.assertFalse(check_update.data_ref.code, msg="Spell Update: Code was not submitted correctly")
        self.assertFalse(check_update.data_ref.start_date, msg="Spell Update: Start date was not submitted correctly")        
        self.assertTrue(check_update.data_ref.patient_id.id == patient_id, msg="Spell Update: Patient id was not registered correctly")
        self.assertTrue(check_update.data_ref.pos_id.id == self.pos_id, msg="Spell Update: Point of Service was not registered correctly")
        self.assertTrue(check_update.data_ref.suggested_location_id.id == self.wt_id, msg="Spell Update: Location id not registered correctly")
        ref_doctors = [refd for refd in check_update.data_ref.ref_doctor_ids]
        con_doctors = [cond for cond in check_update.data_ref.con_doctor_ids]
        self.assertTrue(len(ref_doctors) == 1, msg="Spell Update: Ref Doctors not registered correctly")
        self.assertTrue(len(con_doctors) == 1, msg="Spell Update: Consultant Doctors not registered correctly")
        self.assertTrue(ref_doctors[0].name == "%s, %s" % (update_doctors[1]['family_name'], update_doctors[1]['given_name']), msg="Spell Update: Ref Doctors data not registered correctly")
        self.assertTrue(con_doctors[0].name == "%s, %s" % (update_doctors[0]['family_name'], update_doctors[0]['given_name']), msg="Spell Update: Consultant Doctors data not registered correctly")
        update_ref_doctor = ref_doctors[0].id
        update_con_doctor = con_doctors[0].id        
        # Complete Spell Update
        self.activity_pool.complete(cr, self.adt_id, update_activity_id)
        check_update = self.activity_pool.browse(cr, uid, update_activity_id)
        self.assertTrue(check_update.state == 'completed', msg="Spell Update not completed successfully")
        self.assertTrue(check_update.date_terminated, msg="Spell Update Completed: Date terminated not registered")
        # test spell data
        check_spell = self.spell_pool.browse(cr, uid, spell_id[0])
        self.assertTrue(check_spell.activity_id.state == 'started', msg="Spell Update Completed: Spell state incorrect")
        ref_doctors = [refd.id for refd in check_spell.ref_doctor_ids]
        con_doctors = [cond.id for cond in check_spell.con_doctor_ids]
        self.assertTrue(len(ref_doctors) == 1, msg="Spell Update Completed: Spell Ref Doctors not registered correctly")
        self.assertTrue(len(con_doctors) == 1, msg="Spell Update Completed: Spell Consultant Doctors not registered correctly")
        self.assertTrue(ref_doctors[0] == update_ref_doctor, msg="Spell Update Completed: Spell Ref Doctors not registered correctly")
        self.assertTrue(con_doctors[0] == update_con_doctor, msg="Spell Update Completed: Spell Consultant Doctors not registered correctly")
        
        # Patient Transfer
        transfer_data = {
            'other_identifier': other_identifier,
            'location': 'U'}
        transfer_activity_id = self.transfer_pool.create_activity(cr, self.adt_id, {}, {})
        self.activity_pool.submit(cr, self.adt_id, transfer_activity_id, transfer_data)
        check_transfer = self.activity_pool.browse(cr, self.adt_id, transfer_activity_id)
        
        # test Patient Transfer activity data
        self.assertTrue(check_transfer.data_ref.other_identifier == other_identifier, msg="Patient Transfer: Hospital number not submitted correctly")
        self.assertTrue(check_transfer.data_ref.location == 'U', msg="Patient Transfer: Location was not submitted correctly")
        self.assertFalse(check_transfer.data_ref.patient_identifier, msg="Patient Transfer: NHS number was not submitted correctly")
        self.assertTrue(check_transfer.data_ref.patient_id.id == patient_id, msg="Patient Transfer: Patient id was not registered correctly")
        self.assertTrue(check_transfer.data_ref.location_id.id == self.wu_id, msg="Patient Transfer: Transfer location was not registered correctly")
        self.assertTrue(check_transfer.data_ref.from_location_id.id == self.wt_id, msg="Patient Transfer: Origin location was not registered correctly")
        # Complete Patient Transfer
        self.activity_pool.complete(cr, self.adt_id, transfer_activity_id)
        check_transfer = self.activity_pool.browse(cr, uid, transfer_activity_id)
        self.assertTrue(check_transfer.state == 'completed', msg="Patient Transfer not completed successfully")
        self.assertTrue(check_transfer.date_terminated, msg="Patient Transfer Completed: Date terminated not registered")
        # test spell data
        check_spell = self.spell_pool.browse(cr, uid, spell_id[0])
        self.assertTrue(check_spell.activity_id.state == 'started', msg="Patient Transfer Completed: Spell state incorrect")
        
        # Cancel Transfer
        cancel_transfer_activity_id = self.cancel_transfer_pool.create_activity(cr, self.adt_id, {}, {})
        self.activity_pool.submit(cr, self.adt_id, cancel_transfer_activity_id, {'other_identifier': other_identifier})
        check_cancel_transfer = self.activity_pool.browse(cr, self.adt_id, cancel_transfer_activity_id)
        
        # test Cancel Transfer activity data
        self.assertTrue(check_cancel_transfer.data_ref.other_identifier == other_identifier, msg="Cancel Transfer: Hospital number not submitted correctly")
        self.assertTrue(check_cancel_transfer.data_ref.patient_id.id == patient_id, msg="Cancel Transfer: Patient id was not registered correctly")
        self.assertTrue(check_cancel_transfer.data_ref.last_location_id.id == self.wt_id, msg="Cancel Transfer: Origin location was not registered correctly")
        # Complete Cancel Transfer
        self.activity_pool.complete(cr, self.adt_id, cancel_transfer_activity_id)
        check_cancel_transfer = self.activity_pool.browse(cr, uid, cancel_transfer_activity_id)
        self.assertTrue(check_cancel_transfer.state == 'completed', msg="Cancel Transfer not completed successfully")
        self.assertTrue(check_cancel_transfer.date_terminated, msg="Cancel Transfer Completed: Date terminated not registered")
        # test spell data
        check_spell = self.spell_pool.browse(cr, uid, spell_id[0])
        self.assertTrue(check_spell.activity_id.state == 'started', msg="Cancel Transfer Completed: Spell state incorrect")
        
        # Patient Discharge
        discharge_date = dt.now().strftime(dtf)
        discharge_activity_id = self.discharge_pool.create_activity(cr, self.adt_id, {}, {})
        self.activity_pool.submit(cr, self.adt_id, discharge_activity_id, {'other_identifier': other_identifier, 'discharge_date': discharge_date})
        check_discharge = self.activity_pool.browse(cr, self.adt_id, discharge_activity_id)
        
        # test Patient Discharge activity data
        self.assertTrue(check_discharge.data_ref.other_identifier == other_identifier, msg="Patient Discharge: Hospital number not submitted correctly")
        self.assertTrue(check_discharge.data_ref.discharge_date == discharge_date, msg="Patient Discharge: Discharge date was not submitted correctly")
        self.assertTrue(check_discharge.data_ref.patient_id.id == patient_id, msg="Patient Discharge: Patient id was not registered correctly")
        self.assertTrue(check_discharge.data_ref.pos_id.id == self.pos_id, msg="Patient Discharge: Point of Service was not registered correctly")
        # Complete Patient Discharge
        self.activity_pool.complete(cr, self.adt_id, discharge_activity_id)
        check_discharge = self.activity_pool.browse(cr, uid, discharge_activity_id)
        self.assertTrue(check_discharge.state == 'completed', msg="Patient Discharge not completed successfully")
        self.assertTrue(check_discharge.date_terminated, msg="Patient Discharge Completed: Date terminated not registered")
        # test spell data
        check_spell = self.spell_pool.browse(cr, uid, spell_id[0])
        self.assertTrue(check_spell.activity_id.state == 'completed', msg= "Patient Discharge Completed: Spell state incorrect")
        
        # Cancel Discharge
        cancel_discharge_activity_id = self.cancel_discharge_pool.create_activity(cr, self.adt_id, {}, {})
        self.activity_pool.submit(cr, self.adt_id, cancel_discharge_activity_id, {'other_identifier': other_identifier})
        check_cancel_discharge = self.activity_pool.browse(cr, self.adt_id, cancel_discharge_activity_id)
        
        # test Cancel Discharge activity data
        self.assertTrue(check_cancel_discharge.data_ref.other_identifier == other_identifier, msg="Cancel Discharge: Hospital number not submitted correctly")
        self.assertTrue(check_cancel_discharge.data_ref.patient_id.id == patient_id, msg="Cancel Discharge: Patient id was not registered correctly")
        self.assertTrue(check_cancel_discharge.data_ref.pos_id.id == self.pos_id, msg="Cancel Discharge: Point of Service was not registered correctly")
        self.assertTrue(check_cancel_discharge.data_ref.last_location_id.id == self.wt_id, msg="Cancel Discharge: Origin location was not registered correctly")
        # Complete Cancel Discharge
        self.activity_pool.complete(cr, self.adt_id, cancel_discharge_activity_id)
        check_cancel_discharge = self.activity_pool.browse(cr, uid, cancel_discharge_activity_id)
        self.assertTrue(check_cancel_discharge.state == 'completed', msg="Cancel Discharge not completed successfully")
        self.assertTrue(check_cancel_discharge.date_terminated, msg="Cancel Discharge Completed: Date terminated not registered")
        # test spell data
        check_spell = self.spell_pool.browse(cr, uid, spell_id[0])
        self.assertTrue(check_spell.activity_id.state == 'started', msg= "Cancel Discharge Completed: Spell state incorrect")
        
        # Cancel Admit
        cancel_admit_activity_id = self.cancel_admit_pool.create_activity(cr, self.adt_id, {}, {})
        self.activity_pool.submit(cr, self.adt_id, cancel_admit_activity_id, {'other_identifier': other_identifier})
        check_cancel_admit = self.activity_pool.browse(cr, self.adt_id, cancel_admit_activity_id)
        
        # test cancel admit activity data
        self.assertTrue(check_cancel_admit.data_ref.other_identifier == other_identifier, msg="Cancel Admit: Hospital number not submitted correctly")
        self.assertTrue(check_cancel_admit.data_ref.patient_id.id == patient_id, msg="Cancel Admit: Patient id was not registered correctly")
        self.assertTrue(check_cancel_admit.data_ref.pos_id.id == self.pos_id, msg="Cancel Admit: Point of Service was not registered correctly")
        # Complete Cancel Admit
        self.activity_pool.complete(cr, self.adt_id, cancel_admit_activity_id)
        check_cancel_admit = self.activity_pool.browse(cr, uid, cancel_admit_activity_id)
        self.assertTrue(check_cancel_admit.state == 'completed', msg="Cancel Admit not completed successfully")
        self.assertTrue(check_cancel_admit.date_terminated, msg="Cancel Admit Completed: Date terminated not registered")
        # test spell data
        check_spell = self.spell_pool.browse(cr, uid, spell_id[0])
        self.assertTrue(check_spell.activity_id.state == 'cancelled', msg= "Cancel Admit Completed: Spell state incorrect")

