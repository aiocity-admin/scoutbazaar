# -*- coding: utf-8 -*-

{
    "name" : "Scout Money",
    "summary": 'scout money Website Page',
    "description":"""
        """,
    "version" : "12.0.0.4",
    "author"  : "Geminate Consultancy Services",
    "website" : "http://www.geminatecs.com",
    "depends" : ['scout_vendor','scout_customize','jt_express','delivery_ups','payment_paymaya','delivery_easypost'],
    'data': [
             'data/order_data_scheduled.xml',
             'views/sale_order_scheduler_view.xml',
             ],
    'installable': True,
    'auto_install': False,
}
