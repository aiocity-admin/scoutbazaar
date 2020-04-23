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
from odoo.addons.portal.controllers.web import Home
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from lxml import etree, html
import math
import os
import base64
import uuid
import werkzeug
import json
import requests
_logger = logging.getLogger(__name__)

PPG = 20  # Products Per Page
PPR = 4   # Products Per Row


class AuthSignup(AuthSignupHome):


    @http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
    def web_auth_reset_password(self, *args, **kw):

        qcontext = self.get_auth_signup_qcontext()
        if not qcontext.get('token') and not qcontext.get('reset_password_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                if qcontext.get('token'):
                    self.do_signup(qcontext)
                    return self.web_login(*args, **kw)
                else:
                    login = qcontext.get('login')
                    assert login, _("No login provided.")
                    _logger.info(
                        "Password reset attempt for <%s> by user <%s> from %s",
                        login, request.env.user.login, request.httprequest.remote_addr)
                    request.env['res.users'].sudo().reset_password(login)
                    # qcontext['message'] = _("An email has been sent with credentials to reset your password")
                    qcontext['message'] = _("An email has been sent with credentials to reset your password. Please check your Spam and Junk folders in case you don't receive the reset password message in your Inbox.")
            except UserError as e:
                qcontext['error'] = e.name or e.value
            except SignupError:
                qcontext['error'] = _("Could not reset your password")
                _logger.exception('error when resetting password')
            except Exception as e:
                qcontext['error'] = str(e)

        response = request.render('auth_signup.reset_password', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response
      
    def get_auth_signup_qcontext(self):
        res = super(AuthSignup, self).get_auth_signup_qcontext()
        return res

class Home(Home):
    @http.route()
    def web_login(self, redirect=None, *args, **kw):
        response = super(Home, self).web_login(redirect=redirect, *args, **kw)
        if not redirect and request.params['login_success']:
            if request.env['res.users'].browse(request.uid).has_group('base.group_user'):
                redirect = b'/web?' + request.httprequest.query_string
            else:
                redirect = '/shop'
            return http.redirect_with_hash(redirect)
        return response


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
        
        order_delivery_track_lines_dict_new = {}
        track_line_to_delete = []
        for t_line in order_delivery_track_lines_dict:
            country_name = request.env['res.country'].sudo().search([('code','=',t_line)],limit=1)
            nso_code_line = order.order_line.filtered(lambda m:m.location_id and m.location_id.nso_location_id.country_id.code == t_line)
            all_nso_location = []
            for ord_line in nso_code_line:
                if ord_line.location_id not in all_nso_location:
                    all_nso_location.append(ord_line.location_id)
            for ind_location in  all_nso_location: 
                nso_delivery_line = order.order_line.filtered(lambda r:r.is_nso_delivery_line and r.name == "Total Shipping and Handling Fees(" + ind_location.nso_location_id.name + '-' + country_name.name + ")")
                
                if nso_code_line:
                    if order.partner_shipping_id.country_id.code != t_line and nso_code_line[0].delivery_method.shipping_range == 'local':
                        track_line_to_delete.append(t_line)
                
                if nso_delivery_line:
                    order_delivery_track_lines_dict_new.update({
                                                                t_line : [order_delivery_track_lines_dict[t_line],nso_delivery_line.price_total]
                                                                })
                else:
                    order_delivery_track_lines_dict_new.update({
                                                            t_line : [order_delivery_track_lines_dict[t_line],False]
                                                            })
        
        if track_line_to_delete:
            for del_line in track_line_to_delete:
                if del_line in order_delivery_track_lines_dict_new:
                    del order_delivery_track_lines_dict_new[del_line]
        
        return order_delivery_track_lines_dict_new
    
    @http.route(['/checked/cod/method'], type='json', auth="public", website=True)
    def payment_cod_method(self, acquirer_id):
        acquirer_id = request.env['payment.acquirer'].sudo().search([('id','=',int(acquirer_id))],limit=1)
        order = request.website.sale_get_order()
        if acquirer_id and order:
            print('=========acquirer_id.provider==============',acquirer_id.provider)
            if acquirer_id.provider == 'cod':
                order.is_cod_order = True
                order.recalculate_nso_lines(order)
            else:
                order.is_cod_order = False
                order.recalculate_nso_lines(order)

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
        is_domestic_include_nso_error = False
        vendor_domestic_fees_nso_error = False
        multi_company = request.env['res.config.settings'].sudo().search([],limit=1)
        check_multi_company = multi_company.group_multi_company
        res_config = request.env['payment.handling.config'].sudo().search([],limit=1)
        handling_charge = res_config.handling_charge
        payment_processing_fee = res_config.payment_processing_fee
        transaction_value = res_config.transaction_value
        print('=====order====c========payment--=--',payment_processing_fee)
        nso_delivery_lines = order.order_line.filtered(lambda r:r.is_nso_delivery_line)
        nso_delivery_lines.update({'delivery_charge':0.0})
        if partner_shipping_id:
            for line in order.order_line:
                stage_ids = request.env['stock.location.route'].sudo().search([('name','=','Dropship')])
                if line.product_id.public_categ_ids and not line.product_id.route_ids in stage_ids and line.product_id.product_tmpl_id.type != 'service':
                    stock_locations = request.env['stock.location'].sudo().search([('nso_location_id','=',line.product_id.product_tmpl_id.nso_partner_id.id)])
                    if stock_locations:
                        stock_scout_loc = request.env['scout.stock'].sudo().search([('location_id','in',stock_locations.ids)])
                        if stock_scout_loc:
                            for ss_id in stock_scout_loc:
                                if partner_shipping_id.state_id.id in ss_id.state_ids.ids and partner_shipping_id.country_id == ss_id.country_id:
                                    line.location_id = ss_id.location_id
                            
                            if not line.location_id:
                                stock_scout_country_filter = stock_scout_loc.filtered(lambda r:r.country_id == partner_shipping_id.country_id)
                                if stock_scout_country_filter:
                                    line.location_id = stock_scout_country_filter[0].location_id
                            
                            if not line.location_id:
                                line.location_id = stock_scout_loc[0].location_id
                        
                        if line.location_id.nso_location_id.country_id == partner_shipping_id.country_id:
                            orderlines_country_grouping.update({line.location_id.nso_location_id.country_id:False})
                        else:
                            orderlines_country_grouping.update({line.location_id.nso_location_id.country_id:True})
        order = request.website.sale_get_order()
        for line_group in orderlines_country_grouping:
            if orderlines_country_grouping[line_group]:
                if check_multi_company:
                    delivery_methods = request.env['delivery.carrier'].sudo().search([('company_id','=',request.env.user.company_id.id),('source_country_ids','in',[line_group.id]),('shipping_range','=','international')])
                else:
                    delivery_methods = request.env['delivery.carrier'].sudo().search([('source_country_ids','in',[line_group.id]),('shipping_range','=','international')])
                if delivery_methods:
                    international_shipping_methods.update({line_group.code:delivery_methods})
            else:
                #Same Source Destination Code====================
                nso_same_country_code_group = order.order_line.filtered(lambda n:n.location_id and n.location_id.nso_location_id.country_id.code == order.partner_shipping_id.country_id.code)
                nso_same_country_location_group = {}
                same_carrier = False
                same_delivery_price = 0.0
                if nso_same_country_code_group:
                    if not same_carrier:
                        if check_multi_company:
                            same_carrier = request.env['delivery.carrier'].sudo().search([('company_id','=',request.env.user.company_id.id),('source_country_ids','in',[order.partner_shipping_id.country_id.id]),('shipping_range','=','local')],limit=1)
                        else:
                            same_carrier = request.env['delivery.carrier'].sudo().search([('source_country_ids','in',[order.partner_shipping_id.country_id.id]),('shipping_range','=','local')],limit=1)
                        if not same_carrier:
                            if check_multi_company:
                                same_carrier = request.env['delivery.carrier'].sudo().search([('company_id','=',request.env.user.company_id.id),('source_country_ids','in',[order.partner_shipping_id.country_id.id]),('shipping_range','=','international')],limit=1)
                            else:
                                same_carrier = request.env['delivery.carrier'].sudo().search([('source_country_ids','in',[order.partner_shipping_id.country_id.id]),('shipping_range','=','international')],limit=1)
                for c_group in nso_same_country_code_group:
                    if c_group.location_id in nso_same_country_location_group:
                        nso_same_country_location_group[c_group.location_id] |= c_group
                    else:
                        nso_same_country_location_group.update({c_group.location_id:c_group})
                for nso_loc in nso_same_country_location_group:
                    if same_carrier:
                        res_price = getattr(same_carrier, '%s_rate_line_shipment' % same_carrier.delivery_type)(order,nso_same_country_location_group[nso_loc])
                        print('=========1=====res_price=========',res_price)
                        if res_price.get('error_message'):
                            is_domestic_products = True
                            is_domestic_include_nso_error = True
                            vendor_domestic_fees_nso_error = res_price.get("error_message")
                            nso_same_country_location_group[nso_loc].write({
                                                                       'delivery_method':same_carrier.id,
                                                                       'delivery_charge':0.0,
                                                                       'shipping_charge':0.0,
                                                                       'extra_charge_product':0.0,
                                                                    })
                            order.calculate_nso_lines(order)
                        else:
                            is_domestic_products = True
                            domestic_carrier = same_carrier
                            currency = request.env['res.currency'].sudo().search([('name','=',res_price.get('currency_code'))])
                            if currency:
                                if order.currency_id != order.company_id.currency_id:
                                    payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
                            handling_price = (res_price.get('price') *handling_charge)/100
                            price_total = 0.0
                            for s_line in nso_same_country_location_group[nso_loc]:
                                price_total += s_line.price_total
                            
#                             temp_price = payment_processing_fee + ((transaction_value/100) * (price_total + res_price.get('price') + handling_price))
                            temp_price = ((payment_processing_fee + res_price.get('price') + price_total + handling_price)/ (1 - transaction_value/100) - (payment_processing_fee + res_price.get('price') + price_total + handling_price))
                            same_delivery_price += round((temp_price + res_price.get('price')),2)
                            delivery_price_split = (temp_price + res_price.get('price'))/len(nso_same_country_location_group[nso_loc])
                            shipping_price_split = res_price.get('price')/len(nso_same_country_location_group[nso_loc])
                            extra_charge_split = temp_price/len(nso_same_country_location_group[nso_loc])
                            
                            domestic_price += round((temp_price + res_price.get('price')),2)
                            nso_same_country_location_group[nso_loc].write({
                                                                       'delivery_method':same_carrier.id,
                                                                       'delivery_charge':delivery_price_split,
                                                                       'shipping_charge':shipping_price_split,
                                                                       'extra_charge_product':extra_charge_split,
                                                                    })
                            order.calculate_nso_lines(order)
        if is_domestic_products and not is_domestic_include_nso_error:
            delivery_line_track_ids = request.env['delivery.line.track'].sudo().search([
                                                                                        ('country_id','=',order.partner_shipping_id.country_id.id),
                                                                                        ('order_id','=',order.id),
                                                                                        ],limit=1)
            if delivery_line_track_ids:
                delivery_line_track_ids.update({
                                                'delivery_price': round(domestic_price,2)
                                                })
            else:
                request.env['delivery.line.track'].sudo().create({
                                                                  'country_id':order.partner_shipping_id.country_id.id,
                                                                  'order_id' : order.id,
                                                                  'carrier_id': domestic_carrier.id,
                                                                  'delivery_price':domestic_price,
                                                                  'is_vendor_track':False
                                                                  })
            res.qcontext.update({'domestic_fees': "%.2f" % round(domestic_price, 2),
                                 'vendor_domestic_fees_nso_error': vendor_domestic_fees_nso_error,
                                 })
        if is_domestic_products and is_domestic_include_nso_error:
            res.qcontext.update({'domestic_fees': "%.2f" % round(domestic_price, 2),
                                 'vendor_domestic_fees_nso_error': vendor_domestic_fees_nso_error,
                                 })
        
        
        
        order_delivery_track_lines_dict = {}
        order_delivery_track_lines = request.env['delivery.line.track'].sudo().search([('order_id','=',order.id),('is_vendor_track','=',False)])
        if order_delivery_track_lines:
            for track_line in order_delivery_track_lines:
                order_delivery_track_lines_dict.update({track_line.country_id.code:track_line.carrier_id})
            
            for t_line in order_delivery_track_lines:
                country_id = t_line.country_id
                shipping_lines = order.order_line.filtered(lambda r: r.location_id and r.location_id.nso_location_id.country_id == country_id)
                if shipping_lines:
                    shipping_lines.update({'delivery_method':t_line.carrier_id})
        order = request.website.sale_get_order()
        order_delivery_track_lines_dict = self.prepare_international_shipping_dict(order,order_delivery_track_lines_dict)
        
        len_list = len(international_shipping_methods)
        if len_list:
            for inter_line in international_shipping_methods:
                if not inter_line in order_delivery_track_lines_dict:
                    order = request.website.sale_get_order()
                    country_code = inter_line
                    carrier_id = international_shipping_methods[inter_line][0].id
                    carrier = request.env['delivery.carrier'].sudo().browse(carrier_id)
                    country_id = request.env['res.country'].sudo().search([('code','=',country_code)],limit=1)
                    delivery_price = 0.0
                    res_config = request.env['payment.handling.config'].sudo().search([],limit=1)
                    handling_charge = res_config.handling_charge
                    payment_processing_fee = res_config.payment_processing_fee
                    transaction_value = res_config.transaction_value
                    nso_country_code_group = order.order_line.filtered(lambda n:n.location_id and n.location_id.nso_location_id.country_id.code == country_code)
                    nso_country_location_group = {}
                    for c_group in nso_country_code_group:
                        if c_group.location_id in nso_country_location_group:
                            nso_country_location_group[c_group.location_id] |= c_group
                        else:
                            nso_country_location_group.update({c_group.location_id:c_group})
                    for nso_loc in nso_country_location_group:
                        res_price = getattr(carrier, '%s_rate_line_shipment' % carrier.delivery_type)(order,nso_country_location_group[nso_loc])
                        print('=========2=====res_price=========',res_price)
                        if res_price.get('error_message'):
                            res_price.get("error_message")
                            nso_country_location_group[nso_loc].write({
                                                                       'delivery_method':carrier.id,
                                                                       'delivery_charge':0.0,
                                                                       'shipping_charge':0.0,
                                                                       'extra_charge_product':0.0,
                                                                    })
                            order.calculate_nso_lines(order)
                        else:
                            currency = request.env['res.currency'].sudo().search([('name','=',res_price.get('currency_code'))])
                            if currency:
                                if order.currency_id != order.company_id.currency_id:
                                    payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
                            handling_price = (res_price.get('price') *handling_charge)/100
                            price_total = 0.0
                            for s_line in nso_country_location_group[nso_loc]:
                                price_total += s_line.price_total
                            
#                             temp_price = payment_processing_fee + ((transaction_value/100) * (price_total + res_price.get('price') + handling_price))
                            temp_price = ((payment_processing_fee + res_price.get('price') + price_total + handling_price)/ (1 - transaction_value/100) - (payment_processing_fee + res_price.get('price') + price_total + handling_price))
                            delivery_price += round((temp_price + res_price.get('price')),2)
                            delivery_price_split = (temp_price + res_price.get('price'))/len(nso_country_location_group[nso_loc])
                            shipping_price_split = res_price.get('price')/len(nso_country_location_group[nso_loc])
                            extra_charge_split = temp_price/len(nso_country_location_group[nso_loc])
                            nso_country_location_group[nso_loc].write({
                                                                       'delivery_method':carrier.id,
                                                                       'delivery_charge':delivery_price_split,
                                                                       'shipping_charge':shipping_price_split,
                                                                       'extra_charge_product':extra_charge_split,
                                                                    })
                            order.calculate_nso_lines(order)
                    delivery_line_track_ids = request.env['delivery.line.track'].sudo().search([
                                                                                                ('country_id','=',country_id.id),
                                                                                                ('order_id','=',order.id),
                                                                                                ('is_vendor_track','=',False)
                                                                                            ],limit=1)
                    if delivery_line_track_ids:
                        delivery_line_track_ids.update({
                                                        'carrier_id':carrier.id,
                                                        'delivery_price': delivery_price,
                                                        'is_vendor_track': False
                                                        })
                    else:
                        request.env['delivery.line.track'].sudo().create({
                                                                          'country_id':country_id.id,
                                                                          'order_id' : order.id,
                                                                          'carrier_id': carrier.id,
                                                                          'delivery_price':delivery_price,
                                                                          'is_vendor_track':False
                                                                          })
                    track_id = request.env['delivery.line.track'].sudo().search([
                                                                            ('country_id.code','=',inter_line),
                                                                            ('order_id','=',order.id),
                                                                            ('is_vendor_track','=',False)
                                                                            ],limit=1)
                    
                    if track_id:
                        order_delivery_track_lines_dict.update({
                                                                    inter_line:[carrier,track_id.delivery_price]
                                                                    })
                    else:
                        order_delivery_track_lines_dict.update({
                                                                    inter_line:[carrier,False]
                                                                    })
        
        
        order.recalculate_nso_lines(order)
        order._compute_website_order_line()
        res.qcontext.update({
                             'is_domestic_products':is_domestic_products,
                             'international_shipping_methods':international_shipping_methods,
                             'order_delivery_track_lines_dict':order_delivery_track_lines_dict,
                             })
        order.check_blank_nso_delivery_lines()  
        return res
    
    @http.route(['/get/nso_international_shipping_rates'], type='json', auth="public", website=True)
    def get_nso_international_shipping_rates(self,**post):
        
        order = request.website.sale_get_order()
        country_code = post.get('nso_country_code')
        carrier_id = int(post.get('nso_delivery_id'))
        carrier = request.env['delivery.carrier'].sudo().browse(carrier_id)
        delivery_price = 0.0
        res_config = request.env['payment.handling.config'].sudo().search([],limit=1)
        handling_charge = res_config.handling_charge
        payment_processing_fee = res_config.payment_processing_fee
        transaction_value = res_config.transaction_value
        nso_country_code_group = order.order_line.filtered(lambda n:n.location_id and n.location_id.nso_location_id.country_id.code == country_code)
        nso_country_location_group = {}
        for c_group in nso_country_code_group:
            if c_group.location_id in nso_country_location_group:
                nso_country_location_group[c_group.location_id] |= c_group
            else:
                nso_country_location_group.update({c_group.location_id:c_group})
        for nso_loc in nso_country_location_group:
            res = getattr(carrier, '%s_rate_line_shipment' % carrier.delivery_type)(order,nso_country_location_group[nso_loc])
            if res.get('error_message'):
                return res
            else:
                currency = request.env['res.currency'].sudo().search([('name','=',res.get('currency_code'))])
                if currency:
                    if order.currency_id != order.company_id.currency_id:
                        payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
                handling_price = (res.get('price') *handling_charge)/100
                price_total = 0.0
                for s_line in nso_country_location_group[nso_loc]:
                    price_total += s_line.price_total
                
#                 temp_price = payment_processing_fee + ((transaction_value/100) * (price_total + res.get('price') + handling_price))
                temp_price = ((payment_processing_fee + res.get('price') + price_total + handling_price)/ (1 - transaction_value/100) - (payment_processing_fee + res.get('price') + price_total + handling_price))
                delivery_price += round((temp_price + res.get('price')),2)
#         return {'nso_delivery_price': order.currency_id.symbol + ' ' + str(round(delivery_price,2))}
        return {'nso_delivery_price': order.currency_id.symbol + ' ' + str("%.2f" % round(delivery_price, 2))}
    
    @http.route(['/calculate/international_shipping'], type='json', auth="public", website=True)
    def calculate_international_shipping(self,**post):
        order = request.website.sale_get_order()
        country_code = post.get('country_code')
        carrier_id = int(post.get('delivery_id'))
        carrier = request.env['delivery.carrier'].sudo().browse(carrier_id)
        country_id = request.env['res.country'].sudo().search([('code','=',country_code)],limit=1)
        delivery_price = 0.0
        res_config = request.env['payment.handling.config'].sudo().search([],limit=1)
        handling_charge = res_config.handling_charge
        payment_processing_fee = res_config.payment_processing_fee
        transaction_value = res_config.transaction_value
        value = {}
        is_error_in_change_input = False
        nso_country_code_group = order.order_line.filtered(lambda n:n.location_id and n.location_id.nso_location_id.country_id.code == country_code)
        nso_country_location_group = {}
        for c_group in nso_country_code_group:
            if c_group.location_id in nso_country_location_group:
                nso_country_location_group[c_group.location_id] |= c_group
            else:
                nso_country_location_group.update({c_group.location_id:c_group})
        for nso_loc in nso_country_location_group:
            res = getattr(carrier, '%s_rate_line_shipment' % carrier.delivery_type)(order,nso_country_location_group[nso_loc])
            if res.get('error_message'):
                nso_country_location_group[nso_loc].write({
                                                           'delivery_method':carrier.id,
                                                           'delivery_charge':0.0,
                                                           'shipping_charge':0.0,
                                                           'extra_charge_product':0.0,
                                                        })
                order.calculate_nso_lines(order)
                order = request.website.sale_get_order()
                order._compute_website_order_line()
                res['website_sale.cart_summary'] = request.env['ir.ui.view'].render_template("website_sale.cart_summary",{'website_sale_order':order})
                res['nso_amount_delivery'] = order.currency_id.symbol + ' ' + str(order.nso_amount_delivery)
                return res
            else:
                currency = request.env['res.currency'].sudo().search([('name','=',res.get('currency_code'))])
                if currency:
                    if order.currency_id != order.company_id.currency_id:
                        payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
                handling_price = (res.get('price') *handling_charge)/100
                price_total = 0.0
                for s_line in nso_country_location_group[nso_loc]:
                    price_total += s_line.price_total
                
#                 temp_price = payment_processing_fee + ((transaction_value/100) * (price_total + res.get('price') + handling_price))
                temp_price = ((payment_processing_fee + res.get('price') + price_total + handling_price)/ (1 - transaction_value/100) - (payment_processing_fee + res.get('price') + price_total + handling_price))
                delivery_price += round((temp_price + res.get('price')),2)
                delivery_price_split = (temp_price + res.get('price'))/len(nso_country_location_group[nso_loc])
                shipping_price_split = res.get('price')/len(nso_country_location_group[nso_loc])
                extra_charge_split = temp_price/len(nso_country_location_group[nso_loc])
                nso_country_location_group[nso_loc].write({
                                                           'delivery_method':carrier.id,
                                                           'delivery_charge':delivery_price_split,
                                                           'shipping_charge':shipping_price_split,
                                                           'extra_charge_product':extra_charge_split,
                                                        })
                order.calculate_nso_lines(order)
        delivery_line_track_ids = request.env['delivery.line.track'].sudo().search([
                                                                                    ('country_id','=',country_id.id),
                                                                                    ('order_id','=',order.id),
                                                                                    ('is_vendor_track','=',False)
                                                                                ],limit=1)
        if delivery_line_track_ids:
            delivery_line_track_ids.update({
                                            'carrier_id':carrier.id,
                                            'delivery_price': delivery_price,
                                            'is_vendor_track': False
                                            })
        else:
            request.env['delivery.line.track'].sudo().create({
                                                              'country_id':country_id.id,
                                                              'order_id' : order.id,
                                                              'carrier_id': carrier.id,
                                                              'delivery_price':delivery_price,
                                                              'is_vendor_track':False
                                                              })
        
        
        order = request.website.sale_get_order()
        order._compute_website_order_line()
        value['website_sale.cart_summary'] = request.env['ir.ui.view'].render_template("website_sale.cart_summary",{'website_sale_order':order})
        value['nso_amount_delivery'] = order.currency_id.symbol + ' ' + str("%.2f" % round(order.nso_amount_delivery, 2))
        return value
    
    
    def _get_shop_payment_values(self, order, **kwargs):
        values = super(WebsiteSaleCountrySelect, self)._get_shop_payment_values(order, **kwargs)
        order.recalculate_nso_lines(order)
        order = request.website.sale_get_order()
        values.update({'website_sale_order':order})
        return values
    
    
    @http.route(['/check/all_shipping_are_calculated'], type='json', auth="public", website=True)
    def check_all_shipping_are_calculated(self,**post):
        
        order = request.website.sale_get_order()
        for line in order.order_line:
            if line.location_id:
                if not line.delivery_method:
                    return False
                elif line.delivery_method and line.delivery_charge <= 0:
                    return False
                
        
        return True      
     
    
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

