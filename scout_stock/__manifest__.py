# -*- coding: utf-8 -*-

{
    "name" : "Scount Stock",
    "summary": 'scount stock Website Page',
    "description":"""
        """,
    "version" : "12.0.0.1",
    "author"  : "Geminate Consultancy Services",
    "website" : "http://www.geminatecs.com",
    "depends" : ['jt_express','delivery_ups','scout_customize'],
    'data': ['security/ir.model.access.csv',
             'views/scout_stock.xml',
             'views/res_partner_NSO.xml',
             'views/sale_order_view.xml',
             'views/email_template.xml',
             'views/website_templates.xml',
             ],
    'installable': True,
    'auto_install': False,
}