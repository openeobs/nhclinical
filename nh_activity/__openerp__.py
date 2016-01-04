# Part of NHClinical. See LICENSE file for full copyright and licensing details
# -*- coding: utf-8 -*-
{
    'name': 'NH Activity',
    'version': '0.1',
    'category': 'General',
    'license': 'AGPL-3',
    'summary': '',
    'description': """ Activity Base for NH Activity System """,
    'author': 'Neova Health',
    'website': 'http://www.neovahealth.co.uk/',
    'depends': ['nh_odoo_fixes'],
    'data': [
        'views/activity_view.xml',
        'security/ir.model.access.csv'],
    'application': True,
    'installable': True,
    'active': False,
}
