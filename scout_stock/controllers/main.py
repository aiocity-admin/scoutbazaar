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
    
    
    # Get ProductCountry======================================
    def get_stock_country(self,categ_id):
        catge_dup = categ_id
        if categ_id.parent_id:
            return self.get_stock_country(categ_id.parent_id)
        elif not categ_id.parent_id:
            c_id = request.env['res.country'].sudo().search([('code','=',categ_id.code)],limit=1)
#             return categ_id.name
            if c_id:
                return c_id
            else:
                return False
        else:
            return False
    
    #Get Stock location======================================
    def get_storefront_location(self,categ_id):
        catge_dup = categ_id
        if categ_id.parent_id:
            return self.get_storefront_location(categ_id.parent_id)
        elif not categ_id.parent_id:
            if categ_id.name:
                ss_id = request.env['scout.stock'].sudo().search([('country_id.code','=',categ_id.code)],limit=1)
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
        
        
    
    def prepare_international_shipping_dict(self,order,order_delivery_track_lines_dict):
        
        print("Order==================",order)
        print("Delivery Track Lines------",order_delivery_track_lines_dict)
        order_delivery_track_lines_dict_new = {}
        for t_line in order_delivery_track_lines_dict:
            
            nso_delivery_line = order.order_line.filtered(lambda r:r.is_nso_delivery_line and r.name == t_line + ' NSO')
            if nso_delivery_line:
                order_delivery_track_lines_dict_new.update({
                                                            t_line : [order_delivery_track_lines_dict[t_line],nso_delivery_line.price_total]
                                                            })
            else:
                order_delivery_track_lines_dict_new.update({
                                                            t_line : [order_delivery_track_lines_dict[t_line],False]
                                                            })
        return order_delivery_track_lines_dict_new
        
    #Set Location id on orderline and calculate delivery cost code===============================================================
    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
        res = super(WebsiteSaleCountrySelect,self).payment(**post)
        order = request.website.sale_get_order()
        partner_shipping_id = order.partner_shipping_id
        orderlines_country_grouping = {}
        international_shipping_methods = {}
        domestic_price = 0.0
        is_domestic_products = False
        domestic_carrier = False
        
        nso_delivery_lines = order.order_line.filtered(lambda r:r.is_nso_delivery_line)
        nso_delivery_lines.update({'delivery_charge':0.0})
        if partner_shipping_id:
            for line in order.order_line:
                if line.product_id.public_categ_ids:
                    stock_country = self.get_stock_country(line.product_id.public_categ_ids)
                    if stock_country:
                        if stock_country == partner_shipping_id.country_id:
                            orderlines_country_grouping.update({stock_country:False})
                            if partner_shipping_id.state_id:
                                ss_id = request.env['scout.stock'].sudo().search([('country_id','=',stock_country.id),('state_ids','in',partner_shipping_id.state_id.id)],limit=1)
                                if ss_id:
                                    if not line.product_id.type == 'service':
                                        line.location_id = ss_id.location_id
                                else:
                                    sco_id = request.env['scout.stock'].sudo().search([('country_id','=',stock_country.id)],limit=1)
                                    if sco_id:
                                        if not line.product_id.type == 'service':
                                            line.location_id = sco_id.location_id
                            else:
                                scou_id = request.env['scout.stock'].sudo().search([('country_id','=',stock_country.id)],limit=1)
                                if scou_id:
                                    if not line.product_id.type == 'service':
                                        line.location_id = scou_id.location_id
                        else:
                            orderlines_country_grouping.update({stock_country:True})
                            sc_id = request.env['scout.stock'].sudo().search([('country_id','=',stock_country.id)],limit=1)
                            if sc_id:
                                if not line.product_id.type == 'service':
                                    line.location_id = sc_id.location_id
                                    
                        
        order = request.website.sale_get_order()
        for line_group in orderlines_country_grouping:
            
            if orderlines_country_grouping[line_group]:
                delivery_methods = request.env['delivery.carrier'].sudo().search([('country_ids','in',[line_group.id]),('shipping_range','=','international')])
                if delivery_methods:
                    international_shipping_methods.update({line_group.code:delivery_methods})
            else:
                for o_line in order.order_line:
                    if o_line.location_id:
                        if o_line.location_id.nso_location_id.country_id == order.partner_shipping_id.country_id:
                            if order.partner_shipping_id.country_id.code == 'PH':
                                delivery_carrier = request.env['delivery.carrier'].search([('delivery_type','=','base_on_jt_configuration')],limit=1)
                                if delivery_carrier:
                                    res_price = delivery_carrier.base_on_jt_configuration_rate_shipment(order,o_line)
                                    if not res_price.get('error_message'):
                                        is_domestic_products = True
                                        domestic_carrier = delivery_carrier
                                        domestic_price += res_price.get('price')
                                        o_line.write({
                                                    'delivery_method':delivery_carrier.id,
                                                    'delivery_charge':res_price.get('price')
                                                    })
                                        order.calculate_nso_lines(order)
                            elif order.partner_shipping_id.country_id.code == 'HK':
                                delivery_carrier = request.env['delivery.carrier'].sudo().search([('country_ids','in',[order.partner_shipping_id.country_id.id]),('delivery_type','=','easypost')],limit=1)
                                if delivery_carrier:
                                    res_price = getattr(delivery_carrier, '%s_rate_line_shipment' % delivery_carrier.delivery_type)(order,o_line)
                                    if not res_price.get('error_message'):
                                        domestic_carrier = delivery_carrier
                                        is_domestic_products = True
                                        domestic_price += res_price.get('price')
                                        o_line.write({
                                                    'delivery_method':delivery_carrier.id,
                                                    'delivery_charge':res_price.get('price')
                                                    })
                                        order.calculate_nso_lines(order)
        
        if is_domestic_products:
            delivery_line_track_ids = request.env['delivery.line.track'].sudo().search([
                                                                                        ('country_id','=',order.partner_shipping_id.country_id.id),
                                                                                        ('order_id','=',order.id),
                                                                                        ],limit=1)
            if delivery_line_track_ids:
                delivery_line_track_ids.update({
                                                'delivery_price': domestic_price
                                                })
            else:
                request.env['delivery.line.track'].sudo().create({
                                                                  'country_id':order.partner_shipping_id.country_id.id,
                                                                  'order_id' : order.id,
                                                                  'carrier_id': domestic_carrier.id,
                                                                  'delivery_price':domestic_price,
                                                                  })
            res.qcontext.update({'domestic_fees': domestic_price})
        
        
        
        
        order_delivery_track_lines_dict = {}
        order_delivery_track_lines = request.env['delivery.line.track'].search([('order_id','=',order.id)])
        
        if order_delivery_track_lines:
            for track_line in order_delivery_track_lines:
                order_delivery_track_lines_dict.update({track_line.country_id.code:track_line.carrier_id})
            
            for t_line in order_delivery_track_lines:
                country_id = t_line.country_id
                shipping_lines = order.order_line.filtered(lambda r: r.location_id and r.location_id.nso_location_id.country_id == country_id)
                if shipping_lines:
                    shipping_lines.update({'delivery_method':t_line.carrier_id})
        
        order = request.website.sale_get_order()
        order.recalculate_nso_lines(order)
        order_new = request.website.sale_get_order()
        order._compute_website_order_line()
        order_delivery_track_lines_dict = self.prepare_international_shipping_dict(order,order_delivery_track_lines_dict)
        res.qcontext.update({
                             'is_domestic_products':is_domestic_products,
                             'international_shipping_methods':international_shipping_methods,
                             'order_delivery_track_lines_dict':order_delivery_track_lines_dict,
                             })  
        return res
    
    #Send NSO Email code======================================
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
        
        return views
    
    
    @http.route(['/calculate/international_shipping'], type='json', auth="public", website=True)
    def calculate_international_shipping(self,**post):
        order = request.website.sale_get_order()
        country_code = post.get('country_code')
        carrier_id = int(post.get('delivery_id'))
        carrier = request.env['delivery.carrier'].sudo().browse(carrier_id)
        country_id = request.env['res.country'].sudo().search([('code','=',country_code)],limit=1)
        delivery_price = 0.0
        lines_to_change = {}
        
        
        for line in order.order_line:
            if line.location_id:
                if line.location_id.nso_location_id.country_id.code == country_code:
                    res = getattr(carrier, '%s_rate_line_shipment' % carrier.delivery_type)(order,line)
                    if res.get('error_message'):
                        return res.get("error_message")
                    else:
                        lines_to_change.update({line:res.get('price')})
                        delivery_price += res.get('price')
                        
        if lines_to_change:
            for change_line in lines_to_change:
                line_id = request.env['sale.order.line'].sudo().browse(change_line.id)
                if line_id:
                    line_id.write({
                                    'delivery_method':carrier.id,
                                    'delivery_charge':lines_to_change[change_line]
                                    })
                    order.calculate_nso_lines(order)
            delivery_line_track_ids = request.env['delivery.line.track'].sudo().search([
                                                                                        ('country_id','=',country_id.id),
                                                                                        ('order_id','=',order.id),
                                                                                        ],limit=1)
            if delivery_line_track_ids:
                delivery_line_track_ids.update({
                                                'carrier_id':carrier.id,
                                                'delivery_price': delivery_price})
            else:
                request.env['delivery.line.track'].sudo().create({
                                                                  'country_id':country_id.id,
                                                                  'order_id' : order.id,
                                                                  'carrier_id': carrier.id,
                                                                  'delivery_price':delivery_price,
                                                                  })
        return {'delivery_price':delivery_price}
    
    
    def _get_shop_payment_values(self, order, **kwargs):
        values = super(WebsiteSaleCountrySelect, self)._get_shop_payment_values(order, **kwargs)
        order.recalculate_nso_lines(order)
        order = request.website.sale_get_order()
        values.update({'website_sale_order':order})
        return values
    
    
    
class MyWebsiteSaleDelivery(WebsiteSale):
       
    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
        res = super(MyWebsiteSaleDelivery, self).payment(**post)
        order = request.website.sale_get_order()
        acquirers = res.qcontext.get('acquirers')
        paymaya_visible = True
        acquirers_new = []
        # Paymaya Filter Code================================
        for line in order.order_line:
            if line.location_id:
                if line.location_id.nso_location_id:
                    if line.location_id.nso_location_id.country_id:
                        if line.location_id.nso_location_id.country_id.code != 'PH':
                            paymaya_visible = False
          
        if not paymaya_visible:
            for acq_id in acquirers:
                if not acq_id.provider == 'paymaya':
                    acquirers_new.append(acq_id)
            res.qcontext.update({'acquirers':acquirers_new})
        return res

