# -*- coding: utf-8 -*-
def get_ids_for_patients_without_registrations(cr):
    cr.execute("""
        SELECT id
        FROM nh_clinical_patient as patient
        WHERE NOT EXISTS (
          SELECT patient_id
          FROM nh_clinical_adt_patient_register as register
          WHERE patient.id = register.patient_id
        )
        ;
    """)
    results = cr.fetchall()
    patient_ids = tuple([result[0] for result in results])
    return patient_ids


def create_registrations_for_patients(cr, patient_ids):
    """
    The `title` field is not given a value as there is no way to determine
    what it should be.

    :param cr:
    :param patient_ids:
    :return:
    """
    if len(patient_ids) == 1:
        operator = '='
        patient_ids = patient_ids[0]
    else:
        operator = 'in'

    _create_activities(cr, patient_ids, operator)
    _create_registrations(cr, patient_ids, operator)
    _update_activity_data_refs(cr, patient_ids, operator)


def _create_activities(cr, patient_ids, operator):
    cr.execute("""
                INSERT INTO nh_activity (
                    date_terminated,
                    create_date,
                    write_uid,
                    create_uid,
                    state,
                    write_date,
                    terminate_uid,
                    assign_locked,
                    summary,
                    data_model,
                    patient_id
                  )
                  SELECT 
                    current_timestamp,
                    current_timestamp,
                    {write_uid},
                    {create_uid},
                    'completed',
                    current_timestamp,
                    {terminate_uid},
                    FALSE,
                    'ADT Patient Register',
                    'nh.clinical.adt.patient.register',
                    id
                  FROM nh_clinical_patient as patient
                  WHERE id {operator} {patient_ids}
                  RETURNING id
                ;
            """.format(
        operator=operator,
        patient_ids=patient_ids,
        create_uid=1,
        write_uid=1,
        terminate_uid=1
        )
    )


def _create_registrations(cr, patient_ids, operator):
    cr.execute("""
            INSERT INTO nh_clinical_adt_patient_register (
                create_date, 
                sex,
                patient_identifier,
                ethnicity,
                create_uid,
                middle_names,
                given_name,
                activity_id,
                other_identifier,
                write_date,
                write_uid,
                family_name,
                dob,
                gender,
                patient_id
              )
              SELECT 
                patient.create_date, 
                patient.sex,
                patient.patient_identifier,
                patient.ethnicity,
                {create_uid},
                patient.middle_names,
                patient.given_name,
                activity.id,
                patient.other_identifier,
                current_timestamp,
                {write_uid},
                patient.family_name,
                patient.dob,
                patient.gender,
                patient.id
              FROM nh_clinical_patient as patient
              JOIN nh_activity as activity
                ON patient.id = activity.patient_id
              WHERE patient.id {operator} {patient_ids}
            ;
        """.format(
        operator=operator,
        patient_ids=patient_ids,
        create_uid=1,
        write_uid=1
        )
    )


def _update_activity_data_refs(cr, patient_ids, operator):
    # TODO is this dangerous? It potentially updates all register activities.
    cr.execute("""
        UPDATE nh_activity
        SET data_ref = 'nh.clinical.adt.patient.register,' || register.id
        FROM nh_clinical_adt_patient_register as register
        WHERE nh_activity.patient_id = register.patient_id
          AND register.patient_id {operator} {patient_ids}
    """.format(operator=operator, patient_ids=patient_ids))
