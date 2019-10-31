# -*- coding: utf-8 -*-

{
    "name" : "Scount Stock",
    "summary": 'scount stock Website Page',
    "description":"""
        """,
    "version" : "12.0.0.1",
    "author"  : "Geminate Consultancy Services",
    "website" : "http://www.geminatecs.com",
    "depends" : ['base','sale','website_sale','stock','delivery_ups'],
    'data': ['security/ir.model.access.csv',
             'views/sale_order_view.xml',
             'views/res_partner_NSO.xml',
             'views/scout_stock.xml',
             'views/email_template.xml',
             ],
    'installable': True,
    'auto_install': False,
}