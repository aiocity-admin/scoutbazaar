# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016-Today Geminate Consultancy Services (<http://geminatecs.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
# -*- coding: utf-8 -*-

from odoo import http
from odoo import tools
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from datetime import datetime,timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz
import datetime
import time
from time import gmtime, strftime
from odoo import fields, http, tools, _
import math
import babel.messages.pofile
import base64
import unicodedata
import requests
import json

class CustomerPortalReturnProduct(CustomerPortal):
    
    @http.route(['/check/qty'], type='json', auth="public", website=True)
    def find_qty(self, line_id, **post):
        return_order_line_id = request.env['sale.order.line'].sudo().search([('id','=',int(line_id))])
        a = False
        if return_order_line_id.order_id:
            for ids in return_order_line_id.order_id.picking_ids:
                if ids.state == 'done':
                    if ids.location_dest_id == return_order_line_id.location_id:
                        if ids.move_ids_without_package.product_id == return_order_line_id.product_id:
                            a += int(ids.move_ids_without_package.product_uom_qty)
        if a:
            return int(return_order_line_id.product_uom_qty) - a
        else:
            if return_order_line_id.product_uom_qty:
                a = int(return_order_line_id.product_uom_qty)
                return a
    
    @http.route(['/submit/return-form'], type='http',methods=['GET', 'POST'], auth="public",website=True,csrf=False)
    def submit_return_form(self, **kw):
        return_order_obj = request.env['return.order']
        return_order_id = request.env['sale.order'].sudo().search([('name','=',kw.get('return_sale_order'))])
        if kw.get('input_return_product'):
            return_order_line_id = request.env['sale.order.line'].sudo().search([('id','=',int(kw.get('input_return_product')))])
            if return_order_line_id:
                list = {
                        'sale_order_id': return_order_id.id,
                        'sale_order_line':return_order_line_id.id,
                        'return_qty': kw.get('return_quantity',False),
                        'note':kw.get('return_reason',False),
                        'company_id':return_order_id.company_id.id,
                        'user_id':return_order_id.user_id.id,
                        'team_id':return_order_id.team_id.id,
                    }
                create_return_id = return_order_obj.sudo().create(list)
                return request.redirect("/my/orders")
            else:
                return request.render("scout_customize.return_error_details")
        else:
            return request.render("scout_customize.return_error_details")
    
    def _prepare_portal_layout_values(self):
        values = super(CustomerPortalReturnProduct, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
#          request.env.user.partner_ids

        rSaleOrder = request.env['return.order'].sudo()
#         current_country = int(request.session['country_id'])
#         if current_country:
        return_order_count = rSaleOrder.search_count([('state', 'in', ['draft','confirmed','return','cancel']),('sale_order_id.partner_id','=', partner.id)])
        if return_order_count:
            values.update({
                'return_order_count': return_order_count,
            })
        return values
    
    
    @http.route(['/return/orders'], type='http', auth="user", website=True)
    def portal_my_return_orders(self, **kw):
#         current_country = int(request.session['country_id'])
        partner = request.env.user.partner_id
        values = {}
        if not request.env.user._is_public():
            ReturnSaleOrder = request.env['return.order'].sudo().search([('state', 'in', ['draft','confirmed','return','cancel']),('sale_order_id.partner_id','=', partner.id)])
            values.update({
                'returnorders': ReturnSaleOrder,
                'page_name': 'returnorder',
            })
        return request.render("scout_customize.return_portal_my_orders", values)
        
        