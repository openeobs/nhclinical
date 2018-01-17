from openerp.osv import orm
from openerp import api


class NhClinicalPolicy(orm.AbstractModel):
    """
    Representation of a trust policy. Policies apply to location objects but
    could in the future apply to patients too.
    """

    _cancel_reasons = {}  # Find means of using this in cancel_others
