# -*- coding: utf-8 -*-
import logging

from openerp.addons.nh_clinical.migrations import \
    backdate_registrations, migrate_adt_admit_table

_logger = logging.getLogger(__name__)


def migrate(cr, installed_version):
    patient_ids = \
        backdate_registrations.get_ids_for_patients_without_registrations(cr)
    backdate_registrations.create_registrations_for_patients(cr, patient_ids)

    migrate_adt_admit_table\
        .migrate_adt_admit_patient_id_column_to_registrations(cr)
    migrate_adt_admit_table.remove_patient_id_column_from_adt_admit_table(cr)
