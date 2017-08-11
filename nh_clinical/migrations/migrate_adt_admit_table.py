# -*- coding: utf-8 -*-
def migrate_adt_admit_patient_id_column_to_registrations(cr):
    cr.execute("""
        UPDATE nh_clinical_adt_patient_admit as admit
          SET (patient_id) = (
            SELECT register.id 
            FROM nh_clinical_adt_patient_register as register
            WHERE register.patient_id = admit.patient_id
          )
        ;
    """)


def remove_patient_id_column_from_adt_admit_table(cr):
    cr.execute("""
        ALTER TABLE nh_clinical_adt_patient_admit DROP COLUMN patient_id;
    """)
