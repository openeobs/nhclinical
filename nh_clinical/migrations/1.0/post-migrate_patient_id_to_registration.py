# -*- coding: utf-8 -*-
import logging

from openerp.addons.nh_clinical.migrations import \
    backdate_registrations, migrate_adt_admit_table
from psycopg2 import ProgrammingError

_logger = logging.getLogger(__name__)


def migrate(cr, installed_version):
    if installed_version >= '8.0.1.0':
        _logger.info('nh_clinical module version is {}, so skipping the '
                     '8.0.1.0 migration scripts.'.format(installed_version))
        return
    try:
        patient_ids = \
            backdate_registrations.get_ids_for_patients_without_registrations(
                cr)
        if patient_ids:
            backdate_registrations.create_registrations_for_patients(
                cr, patient_ids)

        migrate_adt_admit_table\
            .migrate_adt_admit_patient_id_column_to_registrations(cr)
        migrate_adt_admit_table.remove_patient_id_column_from_adt_admit_table(
            cr)

        # The registration field has `required=True` which usually sets the
        # not null constraint but the constraint cannot be set if any row has
        # a null value. This means we must manually add the constraint after
        # the migration has run and the registration column has been populated
        # for all rows.
        cr.execute("""
            ALTER TABLE nh_clinical_adt_patient_admit
            ALTER COLUMN registration
            SET NOT NULL
            ;
        """)
    except ProgrammingError:
        cr.rollback()
        _logger.critical('Migration failed. Transaction rolled back.')
        raise
