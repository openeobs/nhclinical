import logging
from openerp.osv import orm, fields, osv
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class nh_clinical_adt_patient_admit(orm.Model):
    """
    Represents the patient admission operation in the patient management
    system. (A01 Message)

    Consulting and referring doctors are expected in the submitted
    values in the following format::

        [...
            {
                'type': 'c' or 'r', 'code': 'code_string,
                'title': 'Mr', 'given_name': 'John',
                'family_name': 'Smith'
            }...
        ]

    If doctor doesn't exist, then a partner is created (but no user is
    created).
    """

    _name = 'nh.clinical.adt.patient.admit'
    _inherit = ['nh.activity.data']
    _description = 'ADT Patient Admit'
    _columns = {
        'location_id': fields.many2one('nh.clinical.location',
                                       'Admission Location'),
        'registration': fields.many2one(
            'nh.clinical.adt.patient.register', 'Registration'
        ),
        'pos_id': fields.many2one('nh.clinical.pos', 'POS', required=True),
        'location': fields.char('Location', size=256),
        'code': fields.char("Code", size=256),
        'start_date': fields.datetime("Admission Date"),
        'other_identifier': fields.char('Hospital Number', size=100),
        'patient_identifier': fields.char('NHS Number', size=100),
        'doctors': fields.text("Doctors")
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Checks the submitted data and then calls
        :meth:`submit<activity.nh_activity.submit>`.

        If a `ward` :mod:`location<base.nh_clinical_location>`
        with the provided code does not exist, it will create a new one.

        Due to this behaviour the user submitting the data must be
        related to a :mod:`point of service<base.nh_clinical_pos>`
        linked to a valid :mod:`location<base.nh_clinical_location>`
        instance of `pos` type, as new Wards will need to be assigned to
        a point of service.

        :returns: ``True``
        :rtype: bool
        """
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        if not user.pos_ids:
            raise osv.except_osv(
                'POS Missing Error!',
                "POS location is not set for user.login = %s!" % user.login
            )
        if not vals.get('location'):
            raise osv.except_osv(
                'Admission Error!',
                'Location must be set for admission!'
            )
        location_pool = self.pool['nh.clinical.location']
        location_id = location_pool.get_by_code(
            cr, uid, vals['location'], auto_create=True, context=context)
        location = location_pool.browse(cr, uid, location_id, context=context)
        patient_pool = self.pool['nh.clinical.patient']
        patient_id = patient_pool.get_patient_id_for_identifiers(
            cr, uid,
            hospital_number=vals.get('other_identifier'),
            nhs_number=vals.get('patient_identifier'),
            context=context
        )
        data = vals.copy()
        data.update(
            {
                'location_id': location_id,
                'patient_id': patient_id.id,
                'pos_id': location.pos_id.id
            }
        )
        return super(nh_clinical_adt_patient_admit, self).submit(
            cr, uid, activity_id, data, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Calls :meth:`complete<activity.nh_activity.complete>` and then
        creates and completes a new
        :mod:`admission<operations.nh_clinical_patient_admission>` to
        the provided location.

        :returns: ``True``
        :rtype: bool
        """
        res = super(nh_clinical_adt_patient_admit, self).complete(
            cr, uid, activity_id, context=context)
        activity_pool = self.pool['nh.activity']
        admission_pool = self.pool['nh.clinical.patient.admission']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        admission_data = {
            'pos_id': activity.data_ref.pos_id.id,
            'patient_id': activity.data_ref.patient_id.id,
            'location_id': activity.data_ref.location_id.id,
            'code': activity.data_ref.code,
            'start_date': activity.data_ref.start_date
        }
        if activity.data_ref.doctors:
            doctor_pool = self.pool['nh.clinical.doctor']
            admission_data.update({'doctors': activity.data_ref.doctors})
            doctor_pool.evaluate_doctors_dict(cr, uid, admission_data,
                                              context=context)
            del admission_data['doctors']
        admission_id = admission_pool.create_activity(
            cr, uid, {'creator_id': activity_id}, admission_data,
            context=context)
        activity_pool.complete(cr, uid, admission_id, context=context)
        spell_id = activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.spell'],
            ['creator_id', '=', admission_id]], context=context)[0]
        activity_pool.write(cr, SUPERUSER_ID, activity_id,
                            {'parent_id': spell_id})
        return res
