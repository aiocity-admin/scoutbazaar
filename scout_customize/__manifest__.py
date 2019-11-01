# -*- coding: utf-8 -*-
{
    "name" : "Scout Customize",
    "summary": 'Scout Customization - Backend and Frontend',
    "description":"""
        """,
    "version" : "12.0.0.1",
    "author"  : "Geminate Consultancy Services",
    "website" : "http://www.geminatecs.com",
    "depends" : ['alan_customize'],
    'data': [
             'security/ir.model.access.csv',
             'views/school_list.xml',
             'views/school_list_template.xml',
             'views/scout_program.xml',
             'views/troop_event_view.xml',
             'views/res_partner.xml',
             ],
    'installable': True,
    'auto_install': False,
}