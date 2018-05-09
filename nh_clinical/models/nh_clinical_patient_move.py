from openerp import models, fields


class NhClinicalPatientMove(models.Model):
    """
    Extension to the model originally declared in `nh_clinical/operations.py`.
    Created purely to make use of the Odoo V8 API which allows setting of
    default values. This was necessary for the `move_datetime` field to default
    to the current server time.
    """
    _inherit = 'nh.clinical.patient.move'

    def _get_current_time(self):
        date_utils_model = self.env['datetime_utils']
        return date_utils_model.get_current_time(as_string=True)

    move_datetime = fields.Datetime(default=_get_current_time)
