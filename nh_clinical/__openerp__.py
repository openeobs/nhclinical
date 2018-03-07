# -*- coding: utf-8 -*-
# Part of NHClinical. See LICENSE file for full copyright and licensing details
{
    'name': 'NH Clinical Core',
    'version': '0.1',
    'category': 'Clinical',
    'license': 'AGPL-3',
    'summary': 'Clinical extension of Odoo.',
    'description': """
        Serves as a bundle for several modules that extend Odoo into the clinical domain.
    """,
    'author': 'Neova Health',
    'website': 'http://www.neovahealth.co.uk/',
    'depends': ['nh_activity', 'hr'],
    'data': [
        'data/data.xml',
        'data/nh_cancel_reasons.xml',
        'views/pos_view.xml',
        'views/location_view.xml',
        'views/patient_view.xml',
        'views/user_view.xml',
        'views/device_view.xml',
        'views/operations_view.xml',
        'views/doctor_view.xml',
        'wizard/placement_wizard_view.xml',
        'views/menuitem.xml',
        'security/ir.model.access.csv',
        'security/adt/ir.model.access.csv',
        'security/operations/ir.model.access.csv',
        'data/change_ward_manager_to_shift_coordinator.xml'
    ],
    'demo': ['data/test/locations.xml', 'data/test/users.xml'],
    'css': [],
    'js': [],
    'qweb': [],
    'images': [],
    'application': True,
    'installable': True,
    'active': False,
}
