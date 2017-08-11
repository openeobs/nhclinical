# -*- coding: utf-8 -*-
def migrate_adt_admit_patient_id_column_to_registrations(cr):
    cr.execute("""
        UPDATE nh_clinical_adt_patient_admit AS admit
          SET registration = register.id 
          FROM (
            SELECT register.id
            FROM nh_clinical_adt_patient_register AS register
            JOIN nh_clinical_adt_patient_admit AS admit
              ON register.patient_id = admit.patient_id
          ) AS register
        ;
    """)


def remove_patient_id_column_from_adt_admit_table(cr):
    cr.execute("""
        ALTER TABLE nh_clinical_adt_patient_admit DROP COLUMN patient_id;
    """)
