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
 
from odoo import fields
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

class GetAllLinesUser(WebsiteSale):
    
    #Set all line users===============================================================
    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
        res = super(GetAllLinesUser,self).payment(**post)
        order = request.website.sale_get_order()
        user_group = []
        for line in order.order_line:
            if line.product_id:
                if line.product_id.nso_partner_id and not line.product_id.is_vendor_product  and line.product_id.product_tmpl_id.type != 'service':
                    nso_user = request.env['res.users'].sudo().search([('partner_id','=',line.product_id.nso_partner_id.id)],limit=1)
                    if nso_user:
                        user_group.append(nso_user.id)
            if not line.location_id:
                stage_ids = request.env['stock.location.route'].sudo().search([('name','=','Dropship')])
                if line.product_id.vendor_user_product and line.product_id.is_vendor_product and line.product_id.route_ids in stage_ids:
                    vendor_user = line.product_id.vendor_user_product
                    if vendor_user:
                        user_group.append(vendor_user.id)
        order.write({'all_line_users' :[(6,0,user_group)]})
        return res