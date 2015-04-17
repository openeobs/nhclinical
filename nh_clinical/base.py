# -*- coding: utf-8 -*-
from openerp.osv import orm, fields, osv
from openerp import SUPERUSER_ID

import logging
_logger = logging.getLogger(__name__)


class ir_model_access(orm.Model):
    _inherit = 'ir.model.access'
    _columns = {
        'perm_responsibility': fields.boolean('NH Clinical Activity Responsibility'),
        }

# Note - This must go before res_company otherwise a new database will not find the new columns
class res_partner(orm.Model):
    _inherit = 'res.partner'
    _columns = {
        'doctor': fields.boolean('Doctor', help="Check this box if this contact is a Doctor"),
        'code': fields.char('Code', size=256),
    }
    _defaults = {
        'notify_email': lambda *args: 'none'
    }

    def create(self, cr, user, vals, context=None):
        return super(res_partner, self).create(cr, user, vals,
                                               context=dict(context or {}, mail_create_nosubscribe=True))


class res_partner_title_extension(orm.Model):
    _inherit = 'res.partner.title'

    def get_title_by_name(self, cr, uid, title, create=True, context=None):
        """
        Searches for the title with the provided name.
        :param create: if True, the title will be created if it does not exist.
        :return: ID of the title. False if it does not exist an create = False
        """
        title = title.replace('.', '').replace(' ', '').lower()
        title_id = self.search(cr, uid, [['name', '=', title]], context=context)
        if not create:
            return title_id[0] if title_id else False
        else:
            if not title_id:
                return self.create(cr, uid, {'name': title}, context=context)
            else:
                return title_id[0]


class res_company(orm.Model):
    _name = 'res.company'
    _inherit = 'res.company'
    _columns = {
        'pos_ids': fields.one2many('nh.clinical.pos', 'company_id', 'Points of Service'),
    }


class res_users(orm.Model):
    _name = 'res.users'
    _inherit = 'res.users'
    _columns = {
        'pos_id': fields.many2one('nh.clinical.pos', 'POS'),
        'location_ids': fields.many2many('nh.clinical.location',
                                         'user_location_rel',
                                         'user_id',
                                         'location_id',
                                         'Parent Locations of Responsibility'),
        'following_ids': fields.many2many('nh.clinical.patient',
                                          'user_patient_rel',
                                          'user_id',
                                          'patient_id',
                                          'Following Patients'),
        'doctor_id': fields.many2one('nh.clinical.doctor', 'Related Doctor')
    }

    def check_pos(self, cr, uid, user_id, exception=False, context=None):
        """
        Checks if the provided user has an assigned Point of Service
        :param exception: boolean.
        :return: if no exception parameter is provided: True if pos is defined. False if not.
                if exception: True if pos is defined. Point of Service Not Defined exception is raised if not.
        """
        user = self.browse(cr, uid, user_id, context=context)
        result = bool(user.pos_id)
        if not exception:
            return result
        else:
            if not result:
                raise osv.except_osv('Point of Service Not Defined!', 'User %s has no POS defined.' % user.name)
            else:
                return result

    def create(self, cr, user, vals, context=None):
        res = super(res_users, self).create(cr, user, vals, context=dict(context or {}, mail_create_nosubscribe=True))
        if 'doctor_id' in vals:
            self.pool['nh.clinical.doctor'].write(cr, user, vals['doctor_id'], {'user_id': res}, context=context)
        return res

    def write(self, cr, uid, ids, values, context=None):
        res = super(res_users, self).write(cr, uid, ids, values, context)
        if values.get('location_ids') or values.get('groups_id'):
            api = self.pool['nh.clinical.api']
            api.update_activity_users(cr, uid, ids)
        if 'doctor_id' in values:
            self.pool['nh.clinical.doctor'].write(cr, uid, values['doctor_id'], {'user_id': ids[0]}, context=context)
        return res


class res_groups(orm.Model):
    _name = 'res.groups'
    _inherit = 'res.groups'

    def write(self, cr, uid, ids, values, context=None):
        res = super(res_groups, self).write(cr, uid, ids, values, context)
        if values.get('users'):
            api = self.pool['nh.clinical.api']
            user_ids = []
            for group in self.browse(cr, uid, isinstance(ids, (list, tuple)) and ids or [ids]):
                user_ids.extend([u.id for u in group.users])
            api.update_activity_users(cr, uid, user_ids)
        return res


class nh_clinical_pos(orm.Model):
    """ Clinical point of service """
    _name = 'nh.clinical.pos'

    _columns = {
        'name': fields.char('Point of Service', size=100, required=True, select=True),
        'code': fields.char('Code', size=256),
        'location_id': fields.many2one('nh.clinical.location', 'POS Location', required=True),
        'company_id': fields.many2one('res.company', 'Company'),
        'lot_admission_id': fields.many2one('nh.clinical.location', 'Admission Location'),
        'lot_discharge_id': fields.many2one('nh.clinical.location', 'Discharge Location'),
        }

    _sql_constraints = [('pos_code_uniq', 'unique(code)', 'The code for a location must be unique!')]


class nh_clinical_context(orm.Model):
    """ Clinical Context, tells us whether a specific policy would be applicable or not to the model.
        i.e. a Location may be in an 'observation loop' context so patients located in it should trigger policies related
            to that context but not trigger policies related to a different context.
    """
    _name = 'nh.clinical.context'
    _columns = {
        'name': fields.char('Name', size=100, required=True, select=True),
        'models': fields.text('Applicable Models')
        #This should be formatted as a python list of the applicable models for the context
    }

    def check_model(self, cr, uid, ids, model, context=None):
        for c in self.browse(cr, uid, ids, context=context):
            if model not in eval(c.models):
                raise osv.except_osv('Error!', model + ' not applicable for context: %s' % c.name)
        return True


class nh_clinical_location(orm.Model):
    """ Clinical LOCATION """

    _name = 'nh.clinical.location'
    _types = [('poc', 'Point of Care'), ('structural', 'Structural'), ('virtual', 'Virtual'), ('pos', 'POS')]
    _usages = [('bed', 'Bed'), ('bay', 'Bay'),('ward', 'Ward'), ('room', 'Room'),('department', 'Department'), ('hospital', 'Hospital')]

    def _get_pos_id(self, cr, uid, ids, field, args, context=None):
        res = {}
        pos_pool = self.pool['nh.clinical.pos']
        for location in self.browse(cr, uid, ids, context):
            pos_location_id = self.search(cr, uid, [['parent_id', '=', False], ['child_ids', 'child_of', location.id]])
            pos_location_id = pos_location_id[0] if pos_location_id else False
            pos_id = pos_pool.search(cr, uid, [['location_id', '=', pos_location_id]])
            res[location.id] = pos_id[0] if pos_id else False
            if not pos_id:
                _logger.debug("pos_id not found for location '%s', id=%s" % (location.code, location.id))
        return res

    def _pos2location_id(self, cr, uid, ids, context=None):
        res = []
        for pos in self.browse(cr, uid, ids, context):
            res.extend(self.pool['nh.clinical.location'].search(cr, uid, [['id', 'child_of', pos.location_id.id]]))
        return res

    def _is_available(self, cr, uid, ids, field, args, context=None):
        res = {}
        for location in self.browse(cr, uid, ids, context):
            available_location_ids = self.get_available_location_ids(cr, uid, usages=[location.usage], context=context)
            res[location.id] = location.id in available_location_ids
        return res

    def _get_patient_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        patient_pool = self.pool['nh.clinical.patient']
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = patient_pool.search(cr, uid, [('current_location_id', 'child_of', loc.id)], context=context)
        return res

    def _get_user_ids(self, cr, uid, location_id, group_names=None, recursive=True, context=None):
        loc = self.browse(cr, uid, location_id, context=context)
        if not group_names:
            group_names = []
        res = []
        if recursive:
            if loc.child_ids:
                for child in loc.child_ids:
                    res += self._get_user_ids(cr, uid, child.id, group_names, context=context)
        for user in loc.user_ids:
            if not group_names:
                res += [user.id]
            elif any([g.name in group_names for g in user.groups_id]):
                res += [user.id]
        return list(set(res))

    def _get_hca_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = self._get_user_ids(cr, uid, loc.id, group_names=['NH Clinical HCA Group'], context=context)
        return res

    def _get_nurse_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = self._get_user_ids(cr, uid, loc.id, group_names=['NH Clinical Nurse Group'], context=context)
        return res

    def _get_wm_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            if loc.usage == 'ward':
                res[loc.id] = self._get_user_ids(cr, uid, loc.id, group_names=['NH Clinical Ward Manager Group'],
                                                 recursive=False, context=context)
            else:
                res[loc.id] = self._get_user_ids(cr, uid, loc.id, group_names=['NH Clinical Ward Manager Group'],
                                                 context=context)
        return res

    def _get_doctor_ids(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = self._get_user_ids(cr, uid, loc.id,
                                             group_names=['NH Clinical Doctor Group',
                                                          'NH Clinical Junior Doctor Group',
                                                          'NH Clinical Consultant Group',
                                                          'NH Clinical Registrar Group'],
                                             context=context)
        return res

    def _get_hcas(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = len(self._get_user_ids(cr, uid, loc.id, group_names=['NH Clinical HCA Group'],
                                                 context=context))
        return res

    def _get_nurses(self, cr, uid, ids, field, args, context=None):
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = len(self._get_user_ids(cr, uid, loc.id, group_names=['NH Clinical Nurse Group'],
                                                 context=context))
        return res

    def _get_waiting_patients(self, cr, uid, ids, field, args, context=None):
        """
        Returns the number of patients waiting to be allocated into a location within the selected location.
        Which means patients that have open patient placement activities related to this location.
        """
        res = {}
        placement_pool = self.pool['nh.clinical.patient.placement']
        for loc in self.browse(cr, uid, ids, context=context):
            res[loc.id] = len(placement_pool.search(cr, uid, [('suggested_location_id', '=', loc.id),
                                                              ('state', 'not in', ['completed', 'cancelled'])]))
        return res

    def _get_child_patients(self, cr, uid, ids, field, args, context=None):
        """
        Returns the number of patients related to the child locations of this location. Number of patients
        related to this location are not included.
        """
        res = {}
        for loc in self.browse(cr, uid, ids, context=context):
            sum = 0
            for child in loc.child_ids:
                sum += len(child.patient_ids)
            res[loc.id] = sum
        return res

    def get_closest_parent_id(self, cr, uid, location_id, usage, context=None):
        """
        Returns the closest parent found in the hierarchy that has the specified usage.
        Returns False if no parent with that usage is found.
        """
        location = self.read(cr, uid, location_id, ['parent_id'], context=context)
        if not location['parent_id']:
            return False
        else:
            parent = self.read(cr, uid, location['parent_id'][0], ['usage'], context=context)
        if parent['usage'] == usage:
            return parent['id']
        else:
            return self.get_closest_parent_id(cr, uid, parent['id'], usage, context=context)

    def _get_name(self, cr, uid, ids, field, args, context=None):
        result = {}
        for location in self.browse(cr, uid, ids, context=context):
            if location.usage == 'ward':
                result[location.id] = location.name
            else:
                parent_id = self.get_closest_parent_id(cr, uid, location.id, 'ward', context=context)
                if parent_id:
                    parent = self.read(cr, uid, parent_id, ['name'], context=context)
                else:
                    parent = False
                result[location.id] = '{0} [{1}]'.format(location.name, parent['name']) if parent else location.name
        return result

    def _is_available_search(self, cr, uid, obj, name, args, domain=None, context=None):
        """
        Allows to search through the method _is_available so the field is_available can be searched.
        It ignores any operand that is not '=' or '!=' because is_available is a boolean and they would not make sense.
        :param args: list of tuples that define the domain of the search with the format: [is_available, operand, value]
        :return [('id', 'in', list of location ids)] that will be used by the orm to filter locations. The actual meaning
                of this is that any location id in the list is to be returned with the specified search domain.
        """
        location_ids = []
        for cond in args:
            available_value = bool(cond[2])
            if cond[1] not in ['=', '!=']:
                continue
            all_ids = self.search(cr, uid, [['usage', '=', 'bed']], context=context)
            available_locations_map = self._is_available(cr, uid, all_ids, 'is_available', None, context=context)
            if cond[1] == '=':
                location_ids += [k for k, v in available_locations_map.items() if v == available_value]
            else:
                location_ids += [k for k, v in available_locations_map.items() if v != available_value]
        return [('id', 'in', location_ids)]


    _columns = {
        'name': fields.char('Location', size=100, required=True, select=True),
        'full_name': fields.function(_get_name, type='char', size=150, string='Full Name'),
        'code': fields.char('Code', size=256),
        'parent_id': fields.many2one('nh.clinical.location', 'Parent Location'),
        'child_ids': fields.one2many('nh.clinical.location', 'parent_id', 'Child Locations'),
        'type': fields.selection(_types, 'Location Type'),
        'usage': fields.selection(_usages, 'Location Usage'),
        'active': fields.boolean('Active'),
        'pos_id': fields.function(_get_pos_id, type='many2one', relation='nh.clinical.pos', string='POS', store={
            'nh.clinical.location': (lambda s, cr, uid, ids, c: s.search(cr, uid, [['id', 'child_of', ids]]), ['parent_id'], 10),
            'nh.clinical.pos': (_pos2location_id, ['location_id'], 5),
            }),
        'company_id': fields.related('pos_id', 'company_id', type='many2one', relation='res.company', string='Company'),
        'is_available': fields.function(_is_available, type='boolean', string='Is Available?', fnct_search=_is_available_search),
        'patient_capacity': fields.integer('Patient Capacity'),
        'patient_ids': fields.function(_get_patient_ids, type='many2many', relation='nh.clinical.patient', string="Patients"),
        'user_ids': fields.many2many('res.users', 'user_location_rel', 'location_id', 'user_id', 'Responsible Users'),
        # aux fields for the view, worth having a SQL model instead?
        'assigned_hca_ids': fields.function(_get_hca_ids, type='many2many', relation='res.users', string="Assigned HCAs"),
        'assigned_nurse_ids': fields.function(_get_nurse_ids, type='many2many', relation='res.users', string="Assigned Nurses"),
        'assigned_wm_ids': fields.function(_get_wm_ids, type='many2many', relation='res.users', string="Assigned Ward Managers"),
        'assigned_doctor_ids': fields.function(_get_doctor_ids, type='many2many', relation='res.users', string="Assigned Doctors"),
        'related_hcas': fields.function(_get_hcas, type='integer', string="Number of related HCAs"),
        'related_nurses': fields.function(_get_nurses, type='integer', string="Number of related Nurses"),
        'waiting_patients': fields.function(_get_waiting_patients, type='integer', string="Number of Waiting Patients"),
        'child_patients': fields.function(_get_child_patients, type='integer', string="Number of Patients from child locations"),
        'context_ids': fields.many2many('nh.clinical.context', 'nh_location_context_rel', 'location_id', 'context_id', string='Related Clinical Contexts')
    }

    _defaults = {
        'active': True,
        'patient_capacity': 1
    }

    _sql_constraints = [('location_code_uniq', 'unique(code)', 'The code for a location must be unique!')]

    def get_available_location_ids(self, cr, uid, usages=None, context=None):
        """
        Get a list of available locations.
        Only returns beds unless specified otherwise.
        """
        if not usages:
            usages = ['bed']
        activity_pool = self.pool['nh.activity']
        open_spell_ids = activity_pool.search(cr, uid, [
            ['data_model', '=', 'nh.clinical.spell'], ['state', '=', 'started']], context=context)
        busy_location_ids = [a.location_id.id if a.location_id.usage == 'bed' else False
                             for a in activity_pool.browse(cr, uid, open_spell_ids, context=context)]
        busy_location_ids = list(set(busy_location_ids))
        return self.search(cr, uid, [['usage', 'in', usages], ['id', 'not in', busy_location_ids]], context=context)

    def switch_active_status(self, cr, uid, location_id, context=None):
        """
        Activates the location if it's inactive. Deactivates it if it's active.
        Added Audit feature by calling Location Activate / Deactivate Activities instead of just writing active field.
        :return: True if successful
        """
        if isinstance(location_id, list):
            location_id = location_id[0]
        location = self.browse(cr, uid, location_id, context=context)
        activity_pool = self.pool['nh.activity']
        activate_pool = self.pool['nh.clinical.location.activate']
        deactivate_pool = self.pool['nh.clinical.location.deactivate']
        if location.active:
            activity_id = deactivate_pool.create_activity(cr, SUPERUSER_ID, {}, {'location_id': location.id}, context=context)
        else:
            activity_id = activate_pool.create_activity(cr, SUPERUSER_ID, {}, {'location_id': location.id}, context=context)
        return activity_pool.complete(cr, uid, activity_id, context=context)

    def check_context_ids(self, cr, uid, context_ids, context=None):
        if isinstance(context_ids[0], list):
            if context_ids[0][0] == 4:
                context_ids = [c[1] for c in context_ids[0]]
            elif context_ids[0][0] == 6:
                context_ids = context_ids[0][2]
        self.pool['nh.clinical.context'].check_model(cr, uid, context_ids, self._name, context=context)
        return True

    def create(self, cr, uid, vals, context=None):
        if vals.get('context_ids'):
            self.check_context_ids(cr, uid, vals.get('context_ids'), context=context)
        return super(nh_clinical_location, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('context_ids'):
            self.check_context_ids(cr, uid, vals.get('context_ids'), context=context)
        return super(nh_clinical_location, self).write(cr, uid, ids, vals, context=context)


class nh_clinical_patient(osv.Model):
    """
    NHClinical Patient object, to store all the parameters of the Patient
    """
    _name = 'nh.clinical.patient'
    _description = "A Patient"

    _inherits = {'res.partner': 'partner_id'}

    _gender = [['BOTH', 'Both'], ['F', 'Female'], ['I', 'Intermediate'],
               ['M', 'Male'], ['NSP', 'Not Specified'], ['U', 'Unknown']]
    _ethnicity = [
        ['A', 'White - British'], ['B', 'White - Irish'], ['C', 'White - Other background'],
        ['D', 'Mixed - White and Black Caribbean'], ['E', 'Mixed - White and Black African'],
        ['F', 'Mixed - White and Asian'], ['G', 'Mixed - Other background'], ['H', 'Asian - Indian'],
        ['J', 'Asian - Pakistani'], ['K', 'Asian - Bangladeshi'], ['L', 'Asian - Other background'],
        ['M', 'Black - Caribbean'], ['N', 'Black - African'], ['P', 'Black - Other background'], ['R', 'Chinese'],
        ['S', 'Other ethnic group'], ['Z', 'Not stated']
    ]

    def _get_fullname(self, vals):
        family_name = vals.get('family_name')
        given_name = vals.get('given_name')
        middle_names = vals.get('middle_names')

        if family_name and (given_name or middle_names):
            family_name_separator = ', '
        else:
            family_name_separator = ''

        if given_name and middle_names:
            given_name_separator = ' '
        else:
            given_name_separator = ''

        #TODO: Make this better and support comma dependency / format etc
        return ''.join([vals.get('family_name', '') or '',
                        family_name_separator,
                        vals.get('given_name', '') or '',
                        given_name_separator,
                        vals.get('middle_names', '') or ''])

    def _get_name(self, cr, uid, ids, fn, args, context=None):
        result = dict.fromkeys(ids, False)
        for r in self.read(cr, uid, ids, ['family_name', 'given_name', 'middle_names'], context=context):
            #TODO This needs to be manipulable depending on locale
            result[r['id']] = self._get_fullname(r)
        return result

    def check_hospital_number(self, cr, uid, hospital_number, exception=False, context=None):
        """
        Checks if there is a patient with the provided Hospital Number
        :param exception: string with values 'True' or 'False'.
        :return: if no exception parameter is provided: True if patient exists. False if not.
                if exception = 'True': Integrity Error exception is raised if patient exists. False if not.
                if exception = 'False': True if patient exists. Patient Not Found exception is raised if not.
        """
        domain = [['other_identifier', '=', hospital_number]]
        result = bool(self.search(cr, uid, domain, context=context))
        if exception:
            if eval(exception) and result:
                raise osv.except_osv('Integrity Error!', 'Patient with Hospital Number %s already exists!'
                                     % hospital_number)
            elif not eval(exception) and not result:
                raise osv.except_osv('Patient Not Found!', 'There is no patient with Hospital Number %s' %
                                     hospital_number)
        return result

    def check_nhs_number(self, cr, uid, nhs_number, exception=False, context=None):
        """
        Checks if there is a patient with the provided NHS Number
        :param exception: string with values 'True' or 'False'.
        :return: if no exception parameter is provided: True if patient exists. False if not.
                if exception = 'True': Integrity Error exception is raised if patient exists. False if not.
                if exception = 'False': True if patient exists. Patient Not Found exception is raised if not.
        """
        domain = [['patient_identifier', '=', nhs_number]]
        result = bool(self.search(cr, uid, domain, context=context))
        if exception:
            if eval(exception) and result:
                raise osv.except_osv('Integrity Error!', 'Patient with NHS Number %s already exists!'
                                     % nhs_number)
            elif not eval(exception) and not result:
                raise osv.except_osv('Patient Not Found!', 'There is no patient with NHS Number %s' %
                                     nhs_number)
        return result

    def update(self, cr, uid, hospital_number, data, context=None):
        """
        Updates patient data receiving a hospital_number as identifier instead of the usual patient_id
        :return: True if successful
        """
        patient_id = self.search(cr, uid, [['other_identifier', '=', hospital_number]], context=context)
        return self.write(cr, uid, patient_id, data, context=context)

    _columns = {
        'current_location_id': fields.many2one('nh.clinical.location', 'Current Location'),
        'partner_id': fields.many2one('res.partner', 'Partner', required=True, ondelete='restrict'),
        'dob': fields.datetime('Date Of Birth'),  # Partner birthdate is NOT a date.
        'sex': fields.selection(_gender, 'Sex'),
        'gender': fields.selection(_gender, 'Gender'),
        'ethnicity': fields.selection(_ethnicity, 'Ethnicity'),
        'patient_identifier': fields.char('Patient Identifier', size=100, select=True, help="NHS Number"),
        'other_identifier': fields.char('Other Identifier', size=100, required=True, select=True,
                                        help="Hospital Number"),

        'given_name': fields.char('Given Name', size=200),
        'middle_names': fields.char('Middle Name(s)', size=200),
        'family_name': fields.char('Family Name', size=200, select=True),
        'full_name': fields.function(_get_name, type='text', string="Full Name"),
        'follower_ids': fields.many2many('res.users',
                                         'user_patient_rel',
                                         'patient_id',
                                         'user_id',
                                         'Followers')
    }

    _defaults = {
        'active': True,
        'name': 'unknown',
        'gender': 'NSP',
        'ethnicity': 'Z'
    }

    # _sql_constraints = [('hospital_number_uniq', 'unique(other_identifier)', 'The hospital number must be unique!'),
    #                     ('nhs_number_uniq', 'unique(patient_identifier)', 'The nhs number must be unique!')]

    def create(self, cr, uid, vals, context=None):
        if not vals.get('name'):
            vals.update({'name': self._get_fullname(vals)})
        return super(nh_clinical_patient, self).create(cr, uid, vals,
                                                       context=dict(context or {}, mail_create_nosubscribe=True))

    def unlink(self, cr, uid, ids, context=None):
        return super(nh_clinical_patient, self).write(cr, uid, ids, {'active': False}, context=context)


#FIXME: This is here to prevent mail message from complaining when creating a user
class mail_message(osv.Model):
    _name = 'mail.message'
    _inherit = 'mail.message'

    def _get_default_from(self, cr, uid, context=None):
        this = self.pool.get('res.users').browse(cr, SUPERUSER_ID, uid, context=context)
        if this.alias_name and this.alias_domain:
            return '%s <%s@%s>' % (this.name, this.alias_name, this.alias_domain)
        elif this.email:
            return '%s <%s>' % (this.name, this.email)
        else:
            return '%s <%s>' % (this.name, 'No email')


class nh_clinical_specialty(orm.Model):

    _name = 'nh.clinical.specialty'
    _description = 'A Clinical Specialty'

    _specialty_groups = [
        ['surgical', 'Surgical Specialties'], ['medical', 'Medical Specialties'], ['psychiatry', 'Psychiatry'],
        ['radiology', 'Radiology'], ['pathology', 'Pathology'], ['other', 'Other']]

    _columns = {
        'name': fields.char('Main Specialty Title', size=150),
        'code': fields.integer('Code'),
        'group': fields.selection(_specialty_groups, 'Specialty Group')
    }


class nh_clinical_doctor(orm.Model):
    _name = 'nh.clinical.doctor'
    _inherits = {'res.partner': 'partner_id'}
    _gender = [['BOTH', 'Both'], ['F', 'Female'], ['I', 'Intermediate'],
               ['M', 'Male'], ['NSP', 'Not Specified'], ['U', 'Unknown']]
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', required=1, ondelete='restrict'),
        'gender': fields.selection(_gender, 'Gender'),
        'gmc': fields.char('GMC', size=10),
        'specialty_id': fields.many2one('nh.clinical.specialty', 'Speciality'),
        'code': fields.char('Regional Code', size=10),
        'user_id': fields.many2one('res.users', 'User Account')
    }
    _defaults = {
        'gender': 'U'
    }

    def create(self, cr, user, vals, context=None):
        res = super(nh_clinical_doctor, self).create(cr, user, vals, context=dict(context or {}, mail_create_nosubscribe=True))
        if 'user_id' in vals:
            self.pool['res.users'].write(cr, user, vals['user_id'], {'doctor_id': res}, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = super(nh_clinical_doctor, self).write(cr, uid, ids, vals, context=context)
        if 'user_id' in vals:
            self.pool['res.users'].write(cr, uid, vals['user_id'], {'doctor_id': ids[0]}, context=context)
        return res