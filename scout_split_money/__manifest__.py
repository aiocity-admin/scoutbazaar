# -*- coding: utf-8 -*-

{
    "name" : "Scout Spilt Money NSO and Vendorwise",
    "summary": 'scout money Website Page',
    "description":"""
        """,
    "version" : "12.0.0.3",
    "author"  : "Geminate Consultancy Services",
    "website" : "http://www.geminatecs.com",
    "depends" : ['scout_stock'],
    'data': [
             'security/ir.model.access.csv',
             'data/order_data_scheduled.xml',
             'views/account_payment_view.xml',
             'views/amount_transferred_history_views.xml',
             ],
    'installable': True,
    'auto_install': False,
}
