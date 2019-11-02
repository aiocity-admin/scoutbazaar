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
 
from odoo import fields as odoo_fields, tools, _
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.website_event.controllers.main import WebsiteEventController
from odoo.addons.website_sale.controllers.main import WebsiteSale
# from odoo.addons.website_scout_baazar.controllers.main import WebsiteSaleCountrySelect
from odoo.addons.alan_customize.controllers.main import WebsiteSale as WebsiteSaleAlan

class VendorPageGetMyLocation(WebsiteSaleAlan):
    
    #Storefront Warehouse Filters======================================
    @http.route(['/check/storefront/warehouse'], type='json', auth="public", website=True)
    def add_storefront_my_warehouse(self,pi_id, **post):
        order = request.website.sale_get_order()
        if order and order.order_line:
            storefront_location_id = order.order_line[0].location_id.id
            p_id = request.env['product.product'].sudo().search([('id','=',int(pi_id))])
            if p_id.product_tmpl_id:
                if p_id.product_tmpl_id.public_categ_ids.is_vendor_category:
                    if order.order_line[0].product_id.is_vendor_product:
                        return False
                    else:
                        return True
                else:
                    get_id = request.env['product.public.category'].get_storefront_category(p_id.product_tmpl_id.public_categ_ids)
                    if get_id.storefront_location_id.id != storefront_location_id:
                        return True
                    else:
                        return False
        else:
            return False


class VendorPage(WebsiteSale):
    @http.route([
            '''/shop''',
            '''/shop/page/<int:page>''',
            '''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>''',
            '''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>/page/<int:page>'''
            '''/shop/brand/<model("product.brand", "[('website_id', 'in', (False, current_website_id))]"):brand>''',
            '''/shop/brand/<model("product.brand", "[('website_id', 'in', (False, current_website_id))]"):brand>/page/<int:page>''',
        ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='',ppg=False,brand=None, **post):
        res = super(VendorPage, self).shop(page, category, search, ppg, **post)
        country_id = int(request.session['country_id'])
        product_country_category = request.env['product.public.category'].sudo().search([('country_id','=',country_id)],limit=1)
        if product_country_category:
            vendor_categs = request.env['product.public.category'].sudo().search([('parent_id','=',product_country_category.id),('is_vendor_category','=',True)])
            if vendor_categs:
                res.qcontext.update({'vendor_categs': vendor_categs})
        return res
    
# class VendorPageGetLocation(WebsiteSaleCountrySelect):
    
#    #Storefront Shop Filters======================================
#     def change_country_pricelist(self,category):
#         if not category.is_vendor_category:
#             storefront_id = self.get_storefront_location(category)
#             country_id = int(request.session['country_id'])
#             storefront_partner = request.env['res.partner'].sudo().search([('storefront_location_id','=',storefront_id)])
#             if storefront_partner:
#                 request.session['website_sale_current_pl'] = storefront_partner.storefront_pricelist.id
#                 request.website.sale_get_order(force_pricelist=storefront_partner.storefront_pricelist.id)
#                 return storefront_partner.storefront_pricelist
#             else:
#                 return False
    
    #Storefront Warehouse Filters======================================
    @http.route(['/check/my/warehouse'], type='json', auth="public", website=True)
    def add_storefront_warehouse(self,pi_id, **post):
        order = request.website.sale_get_order()
        if order and order.order_line:
            storefront_location_id = order.order_line[0].location_id.id
            p_id = request.env['product.product'].sudo().search([('id','=',int(pi_id))])
            if p_id.product_tmpl_id:
                if p_id.product_tmpl_id.public_categ_ids.is_vendor_category:
                    if order.order_line[0].product_id.is_vendor_product:
                        return False
                    else:
                        return True
                else:
                    get_id = request.env['product.public.category'].get_storefront_category(p_id.product_tmpl_id.public_categ_ids)
                    if get_id.storefront_location_id.id != storefront_location_id:
                        return True
                    else:
                        return False
        else:
            return False