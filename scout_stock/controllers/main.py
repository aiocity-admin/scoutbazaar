# -*- coding: utf-8 -*-
# Part of SnepTech. See LICENSE file for full copyright and licensing details.##
##################################################################################

from datetime import datetime
from odoo import http, tools, _
from odoo import api, models, fields, _
import logging
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from werkzeug.exceptions import Forbidden
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website_sale.controllers.main import TableCompute
from odoo.addons.website_sale.controllers.main import QueryURL
from odoo.addons.website_sale.controllers import main
from odoo.addons.website.controllers.main import Website
from odoo.addons.web_editor.controllers.main import Web_Editor
from odoo.addons.web.controllers.main import Session
from odoo.addons.web.controllers.main import Home
from odoo.http import route, request
from odoo.addons.mass_mailing.controllers.main import MassMailController
from odoo.addons.website_event.controllers.main import WebsiteEventController
from odoo.addons.website_sale_coupon.controllers.main import WebsiteSale as WebsiteSaleCoupon
from odoo.addons.website_helpdesk.controllers.main import WebsiteHelpdesk
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.addons.website_sale_delivery.controllers.main import WebsiteSaleDelivery

from lxml import etree, html
import math
import os
import base64
import uuid
import werkzeug
import json
import requests


PPG = 20  # Products Per Page
PPR = 4   # Products Per Row


class WebsiteSaleCountrySelect(WebsiteSale):
    
    
    #ProductCountry Filters======================================
    def get_stock_country(self,categ_id):
        catge_dup = categ_id
        if categ_id.parent_id:
            return self.get_stock_country(categ_id.parent_id)
        elif not categ_id.parent_id:
            c_id = request.env['res.country'].sudo().search([('name','=',categ_id.name)],limit=1)
#             return categ_id.name
            if c_id:
                return c_id
            else:
                return False
        else:
            return False
    
    #Storefront location Filters======================================
    def get_storefront_location(self,categ_id):
        catge_dup = categ_id
        if categ_id.parent_id:
            return self.get_storefront_location(categ_id.parent_id)
        elif not categ_id.parent_id:
            if categ_id.name:
                ss_id = request.env['scout.stock'].sudo().search([('country_id.name','=',categ_id.name)],limit=1)
                if ss_id:
                    if ss_id.location_id:
                        return ss_id.location_id.id
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:
            return False
        
    #Storefront Payment Filters======================================
    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
        res = super(WebsiteSaleCountrySelect,self).payment(**post)
        order = request.website.sale_get_order()
        partner_shipping_id = order.partner_shipping_id
        if partner_shipping_id:
            for line in order.order_line:
                if line.product_id.public_categ_ids:
                    stock_country = self.get_stock_country(line.product_id.public_categ_ids)
                    if stock_country:
                        if stock_country == partner_shipping_id.country_id:
                            if partner_shipping_id.state_id:
                                ss_id = request.env['scout.stock'].sudo().search([('country_id','=',stock_country.id),('state_ids','in',partner_shipping_id.state_id.id)],limit=1)
                                if ss_id:
                                    line.location_id = ss_id.location_id
                                else:
                                    sco_id = request.env['scout.stock'].sudo().search([('country_id','=',stock_country.id)],limit=1)
                                    if sco_id:
                                        line.location_id = sco_id.location_id
                            else:
                                scou_id = request.env['scout.stock'].sudo().search([('country_id','=',stock_country.id)],limit=1)
                                if scou_id:
                                    line.location_id = scou_id.location_id
                        else:
                            sc_id = request.env['scout.stock'].sudo().search([('country_id','=',stock_country.id)],limit=1)
                            if sc_id:
                                line.location_id = sc_id.location_id
        return res
    
    #Storefront Payment Filters======================================
    @http.route(['/shop/confirmation'], type='http', auth="public", website=True)
    def payment_confirmation(self, **post):
        views = super(WebsiteSaleCountrySelect, self).payment_confirmation(**post)
        line_list = []
        sale_order_line_obj = request.env['sale.order.line'].sudo()
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            for line in order.order_line:
                if not line.location_id.id  in line_list:
                    line_list.append(line.location_id.id)
            if line_list:
                ids = sale_order_line_obj.send_sale_order_email(order,line_list)
                
#             if order.is_settled and not order.is_paid_to_warehouse:
#                  
#                 self.create_warehouse_account_move_line(order)
                    
        return views
    
# class WebsiteSaleDelivery(WebsiteSaleDelivery):
    
#     def _update_website_sale_delivery_return(self, order, **post):
#         carrier_id = int(post['carrier_id'])
#         currency = order.currency_id
#         line_amount_delivery = 0.0
#         for line in order.order_line:
#             line_amount_delivery += line.delivery_charge
#         if order:
#             return {'status': order.delivery_rating_success,
#                     'error_message': order.delivery_message,
#                     'carrier_id': carrier_id,
#                     'new_amount_delivery': self._format_amount(line_amount_delivery, currency),
#                     'new_amount_untaxed': self._format_amount(order.amount_untaxed, currency),
#                     'new_amount_tax': self._format_amount(order.amount_tax, currency),
#                     'new_amount_total': self._format_amount(order.amount_total, currency),
#             }
#         return {}
    
    
    
#     def _get_shop_payment_values(self, order, **kwargs):
#         values = super(WebsiteSaleDelivery, self)._get_shop_payment_values(order, **kwargs)
#         has_storable_products = any(line.product_id.type in ['consu', 'product'] for line in order.order_line)
#         print('===============_get_shop_payment_values=============',values)
#         if not order._get_delivery_methods() and has_storable_products:
#             values['errors'].append(
#                 (_('Sorry, we are unable to ship your order'),
#                  _('No shipping method is available for your current order and shipping address. '
#                    'Please contact us for more information.')))
# 
#         if has_storable_products:
#             if order.carrier_id and not order.delivery_rating_success:
#                 order._remove_delivery_line()
# 
#             delivery_carriers = order._get_delivery_methods()
#             values['deliveries'] = delivery_carriers.sudo()
# #             values['deliveries'] = False
#         values['delivery_has_storable'] = has_storable_products
#         values['delivery_action_id'] = request.env.ref('delivery.action_delivery_carrier_form').id
#         return values
    
#     @http.route(['/shop/payment'], type='http', auth="public", website=True)
#     def payment(self, **post):
#         order = request.website.sale_get_order()
#         if order:
#             order._check_order_line_carrier(order)
#         return super(WebsiteSaleDelivery, self).payment(**post)
    
    
    
#     #Storefront Cart Filters======================================
#     @http.route(['/shop/cart'], type='http', auth="public", website=True)
#     def cart(self, access_token=None, revive='', **post):
#          
#         res = super(WebsiteSaleCountrySelect, self).cart(access_token=None, revive='', **post)
#         order = request.website.sale_get_order(force_create=True)
#         country_ids = []
#         for line in order.order_line:
#             if line.product_id.public_categ_ids:
#                 storefront_location = self.get_storefront_location(line.product_id.public_categ_ids)
#                 stock_country = self.get_stock_country(line.product_id.public_categ_ids)
#                 if stock_country:
#                     country_ids.append(stock_country)
#                 if storefront_location:
#                     line.location_id = storefront_location
#                     
#         #======order line in storefront_location wise get groups======================
#         storefront_list = []
#         for line in order.order_line:
#             if line.location_id:
#                 if line.location_id not in storefront_list:
#                     storefront_list.append(line.location_id)
#         line_groups = []
#         for st_id in storefront_list:
#             order_lines = []
#             for line in order.order_line:
#                 if storefront_location:
#                     if line.location_id.id == st_id.id:
#                         order_lines.append(line)
#             line_groups.append(order_lines)
#             print('===========order_lines==============',order_lines)
#         print('===========order_lines==============',line_groups)
#         
#         #======order line in product country wise get groups======================
#         country_list = []
#         for country in country_ids:
#             if country:
#                 if country not in country_list:
#                     country_list.append(country)
#         print('===========order_lines==============',country_list)
#         
#         return res

