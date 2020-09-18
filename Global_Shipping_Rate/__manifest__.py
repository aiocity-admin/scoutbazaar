# -*- coding: utf-8 -*-
{
    'name': "global_shipping_rate",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'depends': ['website_sale_delivery'],
    'version': '0.1',

    # any module necessary for this one to work correctly
    

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/shipping_rate_view.xml',
        'views/templates.xml'
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application':False,
}
