# -*- coding: utf-8 -*-
def migrate_adt_admit_patient_id_column_to_registrations(cr):
    cr.execute("""
        SELECT id, patient_id
        FROM nh_clinical_adt_patient_admit;
    """)
    results = cr.fetchall()

    for result in results:
        register_id = result[0]
        patient_id = result[1]
        cr.execute("""
            UPDATE nh_clinical_adt_patient_admit
            SET registration = (
              SELECT id
              FROM nh_clinical_adt_patient_register AS register
              WHERE patient_id = {}
              ORDER BY id DESC
              LIMIT 1
            )
            WHERE id = {}
            ;
        """.format(patient_id, register_id))


def remove_patient_id_column_from_adt_admit_table(cr):
    cr.execute("""
        ALTER TABLE nh_clinical_adt_patient_admit DROP COLUMN patient_id;
    """)
