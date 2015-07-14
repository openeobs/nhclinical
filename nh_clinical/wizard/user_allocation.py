from openerp.osv import osv, fields
from lxml import etree


def list_diff(a, b):
    b = set(b)
    return [aa for aa in a if aa not in b]


def list_intersect(a, b):
    b = set(b)
    return [aa for aa in a if aa in b]


class staff_allocation_wizard(osv.TransientModel):
    _name = 'nh.clinical.staff.allocation'
    _rec_name = 'create_uid'

    _stages = [['wards', 'My Ward'], ['review', 'De-allocate'], ['users', 'Roll Call'], ['allocation', 'Allocation']]

    _columns = {
        'create_uid': fields.many2one('res.users', 'User Executing the Wizard'),
        'create_date': fields.datetime('Create Date'),
        'stage': fields.selection(_stages, string='Stage'),
        'ward_id': fields.many2one('nh.clinical.location', string='Ward', domain=[['usage', '=', 'ward']]),
        'location_ids': fields.many2many('nh.clinical.location', 'alloc_loc_rel', 'allocation_id', 'location_id',
                                         string='Locations'),
        'user_ids': fields.many2many('res.users', 'alloc_user_rel', 'allocation_id', 'user_id', string='Users',
                                     domain=[['groups_id.name', 'in', ['NH Clinical HCA Group', 'NH Clinical Nurse Group']]]),
        'allocating_ids': fields.many2many('nh.clinical.allocating', 'alloc_allocating_rel', 'allocation_id',
                                           'allocating_id', string='Allocating Locations')
    }
    _defaults = {
        'stage': 'wards'
    }

    def submit_wards(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        wiz = self.browse(cr, uid, ids[0], context=context)
        ward_ids = [wiz.ward_id.id]
        location_pool = self.pool['nh.clinical.location']
        location_ids = location_pool.search(cr, uid, [['id', 'child_of', ward_ids]], context=context)
        self.write(cr, uid, ids, {'stage': 'review', 'location_ids': [[6, 0, location_ids]]}, context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nursing Shift Change',
            'res_model': 'nh.clinical.staff.allocation',
            'res_id': ids[0],
            'view_mode': 'form',
            'target': 'new',
        }

    def deallocate(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        wiz = self.browse(cr, uid, ids[0], context=context)
        user_pool = self.pool['res.users']
        activity_pool = self.pool['nh.activity']
        patient_pool = self.pool['nh.clinical.patient']
        unfollow_pool = self.pool['nh.clinical.patient.unfollow']
        respallocation_pool = self.pool['nh.clinical.user.responsibility.allocation']
        allocating_pool = self.pool['nh.clinical.allocating']

        location_ids = [location.id for location in wiz.location_ids]
        user_ids = user_pool.search(cr, uid, [
            ['groups_id.name', 'in', ['NH Clinical HCA Group', 'NH Clinical Nurse Group',
                                      'NH Clinical Ward Manager Group']]], context=context)
        user_pool.write(cr, uid, user_ids, {'location_ids': [[5, location_ids]]}, context=context)

        activity_id = respallocation_pool.create_activity(cr, uid, {}, {
                'responsible_user_id': uid, 'location_ids': [[6, 0, [wiz.ward_id.id]]]}, context=context)
        activity_pool.complete(cr, uid, activity_id, context=context)

        # Remove patient followers
        patient_ids = patient_pool.search(cr, uid, [['current_location_id', 'in', location_ids]], context=context)
        if patient_ids:
            unfollow_activity_id = unfollow_pool.create_activity(cr, uid, {}, {
                'patient_ids': [[6, 0, patient_ids]]}, context=context)
            activity_pool.complete(cr, uid, unfollow_activity_id, context=context)

        allocating_ids = [allocating_pool.create(cr, uid, {
            'location_id': l.id
        }, context=context) for l in wiz.location_ids if l.usage == 'bed']
        self.write(cr, uid, ids, {'allocating_ids': [[6, 0, allocating_ids]], 'stage': 'users'}, context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nursing Shift Change',
            'res_model': 'nh.clinical.staff.allocation',
            'res_id': ids[0],
            'view_mode': 'form',
            'target': 'new',
        }

    def submit_users(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        self.write(cr, uid, ids, {'stage': 'allocation'}, context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nursing Shift Change',
            'res_model': 'nh.clinical.staff.allocation',
            'res_id': ids[0],
            'view_mode': 'form',
            'target': 'new',
        }

    def complete(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        allocating_pool = self.pool['nh.clinical.allocating']
        respallocation_pool = self.pool['nh.clinical.user.responsibility.allocation']
        activity_pool = self.pool['nh.activity']
        wizard = self.browse(cr, uid, ids[0], context=context)
        allocation = {u.id: [] for u in wizard.user_ids}
        for allocating in allocating_pool.browse(cr, uid, [a.id for a in wizard.allocating_ids], context=context):
            if allocating.nurse_id:
                allocation[allocating.nurse_id.id].append(allocating.location_id.id)
            if allocating.hca_id:
                allocation[allocating.hca_id.id].append(allocating.location_id.id)
        for key in allocation.keys():
            activity_id = respallocation_pool.create_activity(cr, uid, {}, {
                'responsible_user_id': key, 'location_ids': [[6, 0, allocation[key]]]}, context=context)
            activity_pool.complete(cr, uid, activity_id, context=context)
        return {'type': 'ir.actions.act_window_close'}


class staff_reallocation_wizard(osv.TransientModel):
    _name = 'nh.clinical.staff.reallocation'
    _rec_name = 'create_uid'

    _nursing_groups = ['NH Clinical Nurse Group', 'NH Clinical HCA Group']
    _stages = [['users', 'Current Roll Call'], ['allocation', 'Allocation']]

    def _get_default_ward(self, cr, uid, context=None):
        location_pool = self.pool['nh.clinical.location']
        ward_ids = location_pool.search(cr, uid, [['usage', '=', 'ward'], ['user_ids', 'in', [uid]]], context=context)
        if not ward_ids:
            raise osv.except_osv('Shift Management Error!', 'You must be in charge of a ward to do this task!')
        return ward_ids[0]

    def _get_default_users(self, cr, uid, context=None):
        location_pool = self.pool['nh.clinical.location']
        user_pool = self.pool['res.users']
        ward_ids = location_pool.search(cr, uid, [['usage', '=', 'ward'], ['user_ids', 'in', [uid]]], context=context)
        if not ward_ids:
            raise osv.except_osv('Shift Management Error!', 'You must be in charge of a ward to do this task!')
        location_ids = location_pool.search(cr, uid, [['id', 'child_of', ward_ids[0]]], context=context)
        user_ids = user_pool.search(cr, uid, [['groups_id.name', 'in', self._nursing_groups],
                                              ['location_ids', 'in', location_ids]], context=context)
        return user_ids

    def _get_default_locations(self, cr, uid, context=None):
        location_pool = self.pool['nh.clinical.location']
        ward_ids = location_pool.search(cr, uid, [['usage', '=', 'ward'], ['user_ids', 'in', [uid]]], context=context)
        if not ward_ids:
            raise osv.except_osv('Shift Management Error!', 'You must be in charge of a ward to do this task!')
        location_ids = location_pool.search(cr, uid, [['id', 'child_of', ward_ids[0]]], context=context)
        return location_ids

    def _get_default_allocatings(self, cr, uid, context=None):
        location_pool = self.pool['nh.clinical.location']
        allocating_pool = self.pool['nh.clinical.allocating']
        ward_ids = location_pool.search(cr, uid, [['usage', '=', 'ward'], ['user_ids', 'in', [uid]]], context=context)
        if not ward_ids:
            raise osv.except_osv('Shift Management Error!', 'You must be in charge of a ward to do this task!')
        location_ids = location_pool.search(cr, uid, [['id', 'child_of', ward_ids[0]]], context=context)
        locations = location_pool.browse(cr, uid, location_ids, context=context)
        allocating_ids = []
        for l in locations:
            if l.usage != 'bed':
                continue
            nurse_id = False
            hca_id = False
            for u in l.user_ids:
                groups = [g.name for g in u.groups_id]
                nurse_id = u.id if 'NH Clinical Nurse Group' in groups else nurse_id
                hca_id = u.id if 'NH Clinical HCA Group' in groups else hca_id
            allocating_ids.append(allocating_pool.create(cr, uid, {
                'location_id': l.id,
                'nurse_id': nurse_id,
                'hca_id': hca_id
            }, context=context))
        return allocating_ids

    _columns = {
        'create_uid': fields.many2one('res.users', 'User Executing the Wizard'),
        'create_date': fields.datetime('Create Date'),
        'stage': fields.selection(_stages, string='Stage'),
        'ward_id': fields.many2one('nh.clinical.location', string='Ward', domain=[['usage', '=', 'ward']]),
        'user_ids': fields.many2many('res.users', 'realloc_user_rel', 'allocation_id', 'user_id', string='Users',
                                     domain=[['groups_id.name', 'in', ['NH Clinical HCA Group', 'NH Clinical Nurse Group']]]),
        'location_ids': fields.many2many('nh.clinical.location', 'realloc_loc_rel', 'reallocation_id', 'location_id',
                                         string='Locations'),
        'allocating_ids': fields.many2many('nh.clinical.allocating', 'real_allocating_rel', 'reallocation_id',
                                           'allocating_id', string='Allocating Locations')
    }
    _defaults = {
        'stage': 'users',
        'ward_id': _get_default_ward,
        'user_ids': _get_default_users,
        'location_ids': _get_default_locations,
        'allocating_ids': _get_default_allocatings
    }

    def reallocate(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        user_pool = self.pool['res.users']
        patient_pool = self.pool['nh.clinical.patient']
        unfollow_pool = self.pool['nh.clinical.patient.unfollow']
        respallocation_pool = self.pool['nh.clinical.user.responsibility.allocation']
        activity_pool = self.pool['nh.activity']
        wiz = self.browse(cr, uid, ids[0], context=context)
        location_ids = [l.id for l in wiz.location_ids]
        loc_user_ids = user_pool.search(cr, uid, [['groups_id.name', 'in', self._nursing_groups],
                                                  ['location_ids', 'in', location_ids]], context=context)
        user_ids = [u.id for u in wiz.user_ids]
        recompute = False
        for u_id in loc_user_ids:
            if u_id not in user_ids:
                recompute = True
                user = user_pool.browse(cr, uid, u_id, context=context)
                uloc_ids = [l.id for l in user.location_ids]
                loc_ids = list_diff(uloc_ids, location_ids)
                activity_id = respallocation_pool.create_activity(cr, uid, {}, {
                    'responsible_user_id': u_id, 'location_ids': [[6, 0, loc_ids]]}, context=context)
                activity_pool.complete(cr, uid, activity_id, context=context)
                # Remove patient followers
                loc_ids = list_intersect(uloc_ids, location_ids)
                patient_ids = patient_pool.search(cr, uid, [['current_location_id', 'in', loc_ids]], context=context)
                if patient_ids:
                    unfollow_activity_id = unfollow_pool.create_activity(cr, uid, {}, {
                        'patient_ids': [[6, 0, patient_ids]]}, context=context)
                    activity_pool.complete(cr, uid, unfollow_activity_id, context=context)
        self.write(cr, uid, ids, {'stage': 'allocation'}, context=context)
        if recompute:
            allocating_ids = self._get_default_allocatings(cr, uid, context=context)
            self.write(cr, uid, ids, {'allocating_ids': [[6, 0, allocating_ids]]}, context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nursing Re-Allocation',
            'res_model': 'nh.clinical.staff.reallocation',
            'res_id': ids[0],
            'view_mode': 'form',
            'target': 'new',
        }

    def complete(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        allocating_pool = self.pool['nh.clinical.allocating']
        respallocation_pool = self.pool['nh.clinical.user.responsibility.allocation']
        activity_pool = self.pool['nh.activity']
        wizard = self.browse(cr, uid, ids[0], context=context)
        allocation = {u.id: [] for u in wizard.user_ids}
        for allocating in allocating_pool.browse(cr, uid, [a.id for a in wizard.allocating_ids], context=context):
            if allocating.nurse_id:
                allocation[allocating.nurse_id.id].append(allocating.location_id.id)
            if allocating.hca_id:
                allocation[allocating.hca_id.id].append(allocating.location_id.id)
        for key in allocation.keys():
            activity_id = respallocation_pool.create_activity(cr, uid, {}, {
                'responsible_user_id': key, 'location_ids': [[6, 0, allocation[key]]]}, context=context)
            activity_pool.complete(cr, uid, activity_id, context=context)
        return {'type': 'ir.actions.act_window_close'}


class doctor_allocation_wizard(osv.TransientModel):
    _name = 'nh.clinical.doctor.allocation'
    _rec_name = 'create_uid'

    _stages = [['review', 'De-allocate'], ['users', 'Medical Roll Call']]
    _doctor_groups = ['NH Clinical Doctor Group', 'NH Clinical Junior Doctor Group', 'NH Clinical Consultant Group',
                      'NH Clinical Registrar Group']

    def _get_default_ward(self, cr, uid, context=None):
        location_pool = self.pool['nh.clinical.location']
        ward_ids = location_pool.search(cr, uid, [['usage', '=', 'ward'], ['user_ids', 'in', [uid]]], context=context)
        if not ward_ids:
            raise osv.except_osv('Shift Management Error!', 'You must be in charge of a ward to do this task!')
        return ward_ids[0]

    def _get_default_locations(self, cr, uid, context=None):
        location_pool = self.pool['nh.clinical.location']
        ward_ids = location_pool.search(cr, uid, [['usage', '=', 'ward'], ['user_ids', 'in', [uid]]], context=context)
        if not ward_ids:
            raise osv.except_osv('Shift Management Error!', 'You must be in charge of a ward to do this task!')
        location_ids = location_pool.search(cr, uid, [['id', 'child_of', ward_ids[0]]], context=context)
        return location_ids

    def _get_current_doctors(self, cr, uid, context=None):
        location_pool = self.pool['nh.clinical.location']
        user_pool = self.pool['res.users']
        ward_ids = location_pool.search(cr, uid, [['usage', '=', 'ward'], ['user_ids', 'in', [uid]]], context=context)
        if not ward_ids:
            raise osv.except_osv('Shift Management Error!', 'You must be in charge of a ward to do this task!')
        doctor_ids = user_pool.search(cr, uid, [['groups_id.name', 'in', self._doctor_groups],
                                                ['location_ids', 'in', ward_ids]], context=context)
        return doctor_ids

    _columns = {
        'create_uid': fields.many2one('res.users', 'User Executing the Wizard'),
        'create_date': fields.datetime('Create Date'),
        'stage': fields.selection(_stages, string='Stage'),
        'ward_id': fields.many2one('nh.clinical.location', string='Ward', domain=[['usage', '=', 'ward']]),
        'doctor_ids': fields.many2many('res.users', 'docalloc_doc_rel', 'allocation_id', 'user_id',
                                       string='Current Doctors'),
        'location_ids': fields.many2many('nh.clinical.location', 'docalloc_loc_rel', 'allocation_id', 'location_id',
                                         string='Locations'),
        'user_ids': fields.many2many('res.users', 'docalloc_user_rel', 'allocation_id', 'user_id', string='Users',
                                     domain=[['groups_id.name', 'in', _doctor_groups]])
    }
    _defaults = {
        'stage': 'review',
        'ward_id': _get_default_ward,
        'location_ids': _get_default_locations,
        'doctor_ids': _get_current_doctors
    }

    def deallocate(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        wiz = self.browse(cr, uid, ids[0], context=context)
        user_pool = self.pool['res.users']
        location_ids = [location.id for location in wiz.location_ids]
        user_ids = user_pool.search(cr, uid, [['groups_id.name', 'in', self._doctor_groups]], context=context)
        user_pool.write(cr, uid, user_ids, {'location_ids': [[5, location_ids]]}, context=context)
        self.write(cr, uid, ids, {'stage': 'users'}, context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Medical Shift Change',
            'res_model': 'nh.clinical.doctor.allocation',
            'res_id': ids[0],
            'view_mode': 'form',
            'target': 'new',
        }

    def submit_users(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        wiz = self.browse(cr, uid, ids[0], context=context)
        respallocation_pool = self.pool['nh.clinical.user.responsibility.allocation']
        activity_pool = self.pool['nh.activity']
        for doctor in wiz.user_ids:
            activity_id = respallocation_pool.create_activity(cr, uid, {}, {
                'responsible_user_id': doctor.id, 'location_ids': [[6, 0, [wiz.ward_id.id]]]
            }, context=context)
            activity_pool.complete(cr, uid, activity_id, context=context)
        return {'type': 'ir.actions.act_window_close'}


class allocating_user(osv.TransientModel):
    _name = 'nh.clinical.allocating'
    _rec_name = 'location_id'

    _columns = {
        'location_id': fields.many2one('nh.clinical.location', 'Location', required=1),
        'patient_ids': fields.related('location_id', 'patient_ids', type='many2many', relation='nh.clinical.patient',
                                      string='Patient'),
        'nurse_id': fields.many2one('res.users', 'Responsible Nurse',
                                    domain=[['groups_id.name', 'in', ['NH Clinical Nurse Group']]]),
        'hca_id': fields.many2one('res.users', 'Responsible HCA',
                                  domain=[['groups_id.name', 'in', ['NH Clinical HCA Group']]]),
        'nurse_name': fields.related('nurse_id', 'name', type='char', size=100, string='Responsible Nurse'),
        'hca_name': fields.related('hca_id', 'name', type='char', size=100, string='Responsible HCA')
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(allocating_user, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        allocation_pool = self.pool['nh.clinical.staff.allocation']
        reallocation_pool = self.pool['nh.clinical.staff.reallocation']
        al_id = allocation_pool.search(cr, uid, [['create_uid', '=', uid]], order='id desc')
        real_id = reallocation_pool.search(cr, uid, [['create_uid', '=', uid]], order='id desc')
        allocation = True if al_id else False
        if al_id and real_id:
            al = allocation_pool.browse(cr, uid, al_id[0], context=context)
            real = reallocation_pool.browse(cr, uid, real_id[0], context=context)
            allocation = True if al.create_date > real.create_date else False
        if not (al_id or real_id) or view_type != 'form':
            return res
        else:
            if allocation:
                allocation = allocation_pool.browse(cr, uid, al_id[0], context=context)
                user_ids = [u.id for u in allocation.user_ids]
                res['fields']['nurse_id']['domain'] = [['id', 'in', user_ids], ['groups_id.name', 'in', ['NH Clinical Nurse Group']]]
                res['fields']['hca_id']['domain'] = [['id', 'in', user_ids], ['groups_id.name', 'in', ['NH Clinical HCA Group']]]
            else:
                reallocation = reallocation_pool.browse(cr, uid, real_id[0], context=context)
                user_ids = [u.id for u in reallocation.user_ids]
                res['fields']['nurse_id']['domain'] = [['id', 'in', user_ids], ['groups_id.name', 'in', ['NH Clinical Nurse Group']]]
                res['fields']['hca_id']['domain'] = [['id', 'in', user_ids], ['groups_id.name', 'in', ['NH Clinical HCA Group']]]
        return res


class user_allocation_wizard(osv.TransientModel):
    _name = 'nh.clinical.user.allocation'

    _stages = [['wards', 'Select Wards'], ['users', 'Select Users'], ['allocation', 'Allocation']]

    _columns = {
        'create_uid': fields.many2one('res.users', 'User Executing the Wizard'),
        'stage': fields.selection(_stages, string='Stage'),
        'ward_ids': fields.many2many('nh.clinical.location', 'allocation_ward_rel', 'allocation_id', 'location_id',
                                     string='Wards', domain=[['usage', '=', 'ward']]),
        'user_ids': fields.many2many('res.users', 'allocation_user_rel', 'allocation_id', 'user_id', string='Users'),
    }
    _defaults = {
        'stage': 'users'
    }

    # def submit_users(self, cr, uid, ids, context=None):
    #     allocating_user_pool = self.pool['nh.clinical.allocating.user']
    #     wizard = self.browse(cr, uid, ids[0], context=context)
    #     aluser_ids = [allocating_user_pool.create(cr, uid, {
    #         'user_id': user.id,
    #         'location_ids': [[6, 0, [l.id for l in user.location_ids]]]
    #     }, context=context) for user in wizard.user_ids]
    #     self.write(cr, uid, ids, {'allocating_user_ids': [[6, 0, aluser_ids]], 'stage': 'allocation'})
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Allocation',
    #         'res_model': 'nh.clinical.user.allocation',
    #         'res_id': ids[0],
    #         'view_mode': 'form',
    #         'target': 'new', # change to current to make it look like Joe's design
    #     }
    #
    # def complete(self, cr, uid, ids, context=None):
    #     allocating_user_pool = self.pool['nh.clinical.allocating.user']
    #     respallocation_pool = self.pool['nh.clinical.user.responsibility.allocation']
    #     activity_pool = self.pool['nh.activity']
    #     wizard = self.browse(cr, uid, ids[0], context=context)
    #     for auser in allocating_user_pool.browse(cr, uid, [u.id for u in wizard.allocating_user_ids], context=context):
    #         location_ids = [l.id for l in auser.location_ids]
    #         activity_id = respallocation_pool.create_activity(cr, uid, {}, {
    #             'responsible_user_id': auser.user_id.id, 'location_ids': [[6, 0, location_ids]]}, context=context)
    #         activity_pool.complete(cr, uid, activity_id, context=context)
    #     # TODO: If view target is current then need to set to go back a page?
    #     return {'type': 'ir.actions.act_window_close'}
    #
    # def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
    #     if view_type == 'form' and toolbar:
    #         res = super(user_allocation_wizard, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
    #         doc = etree.XML(res['arch'])
    #         form_nodes = doc.xpath("//form")
    #         for form_node in form_nodes:
    #             form_node.set('edit', '0')
    #             form_node.set('create', '0')
    #             form_node.set('delete', '0')
    #         close_nodes = doc.xpath("//button[@string='Close']")
    #         for close_node in close_nodes:
    #             close_node.getparent().remove(close_node)
    #         res['arch'] = etree.tostring(doc)
    #         return res
    #     else:
    #         return super(user_allocation_wizard, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)