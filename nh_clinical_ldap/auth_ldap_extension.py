# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
from openerp.osv import orm
import logging

_logger = logging.getLogger(__name__)


class NHClinicalLDAPExtension(orm.Model):

    _name = 'res.company.ldap'
    _inherit = 'res.company.ldap'

    def map_ldap_attributes(self, cr, uid, conf, login, ldap_entry,
                            context=None):
        """
        Compose values for a new resource of model res_users,
        based upon the retrieved ldap entry and the LDAP settings.

        :param dict conf: LDAP configuration
        :param login: the new user's login
        :param tuple ldap_entry: single LDAP result (dn, attrs)
        :return: parameters for a new resource of model res_users
        :rtype: dict
        """

        category_pool = self.pool['res.partner.category']
        location_pool = self.pool['nh.clinical.location']
        pos_pool = self.pool['nh.clinical.pos']

        hospital = location_pool.search(cr, uid, [['usage', '=', 'hospital']],
                                        context=context)
        pos = pos_pool.search(cr, uid, [['location_id', 'in', hospital]],
                              context=context)
        hca_group = category_pool.search(cr, uid, [['name', '=', 'HCA']],
                                         context=context)

        if len(ldap_entry) < 2:
            raise ValueError('LDAP Entry does not contain second element')
        if len(ldap_entry[1].get('cn')) < 1:
            raise ValueError('LDAP Entry CN does not contain elements')

        values = {'name': ldap_entry[1]['cn'][0],
                  'login': login,
                  'company_id': conf.get('company'),
                  'ward_ids': [[6, 0, []]],
                  'pos_ids': [[6, 0, pos]],
                  'category_id': [[6, 0, hca_group]]
                  }
        return values
