# -*- coding: utf-8 -*-
###############################################################################
#
#   Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#   Copyright (C) 2016-today Geminate Consultancy Services (<http://geminatecs.com>).
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Australia Post Carrier',
    'summary': """ """,
    "version" : "12.0.0.1",
    "author"  : "Geminate Consultancy Services",
    "website" : "http://www.geminatecs.com",
    'category': 'Sales',
    'depends': ['scout_stock'],
    'license': 'AGPL-3',
    'data': [
            'views/delivery_aus_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}   
