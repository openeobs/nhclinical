import logging

from openerp.osv import orm, fields

_logger = logging.getLogger(__name__)


class nh_clinical_adt_patient_update(orm.Model):
    """
    Represents the patient update operation in the patient management
    system. (A31 Message)
    """

    _name = 'nh.clinical.adt.patient.update'
    _inherit = ['nh.activity.data']
    _description = 'ADT Patient Update'

    _gender = [
        ['BOTH', 'Both'],
        ['F', 'Female'],
        ['I', 'Intermediate'],
        ['M', 'Male'],
        ['NSP', 'Not Specified'],
        ['U', 'Unknown']
    ]
    _ethnicity = [
        ['A', 'White - British'],
        ['B', 'White - Irish'],
        ['C', 'White - Other background'],
        ['D', 'Mixed - White and Black Caribbean'],
        ['E', 'Mixed - White and Black African'],
        ['F', 'Mixed - White and Asian'],
        ['G', 'Mixed - Other background'],
        ['H', 'Asian - Indian'],
        ['J', 'Asian - Pakistani'],
        ['K', 'Asian - Bangladeshi'],
        ['L', 'Asian - Other background'],
        ['M', 'Black - Caribbean'],
        ['N', 'Black - African'],
        ['P', 'Black - Other background'],
        ['R', 'Chinese'],
        ['S', 'Other ethnic group'],
        ['Z', 'Not stated']
    ]

    _columns = {
        'patient_id': fields.many2one('nh.clinical.patient', 'Patient',
                                      required=True),
        'patient_identifier': fields.char('NHS Number', size=10),
        'other_identifier': fields.char('Hospital Number', size=50),
        'family_name': fields.char('Last Name', size=200),
        'given_name': fields.char('First Name', size=200),
        'middle_names': fields.char('Middle Names', size=200),
        'dob': fields.datetime('Date of Birth'),
        'gender': fields.selection(_gender, string='Gender'),
        'sex': fields.selection(_gender, string='Sex'),
        'ethnicity': fields.selection(_ethnicity, string='Ethnicity'),
        'title': fields.many2one('res.partner.title', 'Title')
    }

    def submit(self, cr, uid, activity_id, vals, context=None):
        """
        Handle submission of update data and verify it

        :param vals: Values to update patient record with
        """
        patient_model = self.pool['nh.clinical.patient']
        title_pool = self.pool['res.partner.title']
        patient = patient_model.get_patient_for_identifiers(
            cr, uid,
            hospital_number=vals.get('other_identifier'),
            nhs_number=vals.get('patient_identifier'),
            context=context
        )
        vals['patient_id'] = patient.id
        if vals.get('title') and not isinstance(vals.get('title'), int):
            vals['title'] = title_pool.get_title_by_name(
                cr, uid, vals['title'], context=context)
        return super(nh_clinical_adt_patient_update, self).submit(
            cr, uid, activity_id, vals, context=context)

    def complete(self, cr, uid, activity_id, context=None):
        """
        Overwrites the target :mod:`patient<base.nh_clinical_patient>`
        instance information and then calls
        :meth:`complete<activity.nh_activity.complete>`.

        :returns: ``True``
        :rtype: bool
        """
        activity_pool = self.pool['nh.activity']
        activity = activity_pool.browse(cr, uid, activity_id, context=context)
        patient_pool = self.pool['nh.clinical.patient']
        vals = {
            'title': activity.data_ref.title.id,
            'patient_identifier': activity.data_ref.patient_identifier,
            'other_identifier': activity.data_ref.other_identifier,
            'family_name': activity.data_ref.family_name,
            'given_name': activity.data_ref.given_name,
            'middle_names': activity.data_ref.middle_names,
            'dob': activity.data_ref.dob,
            'gender': activity.data_ref.gender,
            'sex': activity.data_ref.sex,
            'ethnicity': activity.data_ref.ethnicity
        }
        res = patient_pool.write(
            cr, uid, activity.data_ref.patient_id.id, vals, context=context)
        super(nh_clinical_adt_patient_update, self).complete(
            cr, uid, activity_id, context)
        return res
