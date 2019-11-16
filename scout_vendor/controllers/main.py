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
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.website_event.controllers.main import WebsiteEventController
from odoo.addons.website_sale.controllers.main import WebsiteSale
# from odoo.addons.website_scout_baazar.controllers.main import WebsiteSaleCountrySelect
from odoo.addons.alan_customize.controllers.main import WebsiteSale as WebsiteSaleAlan

class VendorPage(WebsiteSale):
    
    # Get vendor======================================
    def get_stock_vendor(self,order,line):
        partner_shipping_id = order.partner_shipping_id
        partner_country_state = line.product_id.international_ids.filtered(lambda r: r.country_id == partner_shipping_id.country_id and r.state_id == partner_shipping_id.state_id)
        if partner_country_state:
            return partner_country_state
        else:
            partner_country = line.product_id.international_ids.filtered(lambda r: r.country_id == partner_shipping_id.country_id)
            if partner_country:
                return partner_country
            else:
                return line.product_id.international_ids[0]
    
    #========= set delivery line track group===============
    def prepare_international_shipping_vendor_dict(self,order,order_delivery_track_lines_dict):
        order_delivery_track_lines_dict_new = {}
        for t_line in order_delivery_track_lines_dict:
            track_id = request.env['delivery.line.track'].sudo().search([
                                                                            ('country_id.code','=',t_line),
                                                                            ('order_id','=',order.id),
                                                                            ('is_vendor_track','=',True)
                                                                            ],limit=1)
            if track_id:
                order_delivery_track_lines_dict_new.update({
                                                            t_line : [order_delivery_track_lines_dict[t_line],track_id.delivery_price]
                                                            })
            else:
                order_delivery_track_lines_dict_new.update({
                                                            t_line : [order_delivery_track_lines_dict[t_line],False]
                                                            })
        return order_delivery_track_lines_dict_new
    
    #Set Location id on orderline and calculate delivery cost code===============================================================
    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
        res = super(VendorPage,self).payment(**post)
        order = request.website.sale_get_order()
        orderlines_vendor_country_grouping = {}
        international_vendor_shipping_methods = {}
        is_domestic_vendor_products = False
        domestic_vendor_carrier = False
        domestic_vendor_price = 0.0
        is_domestic_include_error = False
        is_international_include_error = False
        vendor_domestic_fees_error = False
        res_config = request.env['payment.handling.config'].sudo().search([],limit=1)
        handling_charge = res_config.handling_charge
        payment_processing_fee = res_config.payment_processing_fee
        transaction_value = res_config.transaction_value
        if order.partner_shipping_id:
            for line in order.order_line:
                stage_ids = request.env['stock.location.route'].sudo().search([('name','=','Dropship')])
                if not line.location_id and line.product_id.route_ids in stage_ids and line.product_id.product_tmpl_id.type != 'service':
                    vendor = self.get_stock_vendor(order,line)
                    if vendor:
                        if vendor.country_id == order.partner_shipping_id.country_id:
                            orderlines_vendor_country_grouping.update({vendor.country_id:False})
                        else:
                            orderlines_vendor_country_grouping.update({vendor.country_id:True})
        order = request.website.sale_get_order()
        for line_group in orderlines_vendor_country_grouping:
            if orderlines_vendor_country_grouping[line_group]:
                delivery_methods = request.env['delivery.carrier'].sudo().search([('source_country_ids','in',[line_group.id]),('shipping_range','=','international')])
                if delivery_methods:
                    international_vendor_shipping_methods.update({line_group.code:delivery_methods})
            else:
                #Same Source Destination Code====================
                stage_ids = request.env['stock.location.route'].sudo().search([('name','=','Dropship')])
                vendor_country_code_group = order.order_line.filtered(lambda n: not n.location_id and n.product_id.route_ids in stage_ids)
                vendor_country_based_group = {}
                same_carrier = False
                for v_group in vendor_country_code_group:
                    vendor = self.get_stock_vendor(order,v_group)
                    if vendor in vendor_country_based_group:
                        vendor_country_based_group[vendor] |= v_group
                    else:
                        vendor_country_based_group.update({vendor:v_group})
                        
                if vendor_country_code_group:
                    same_carrier = request.env['delivery.carrier'].sudo().search([('source_country_ids','in',[order.partner_shipping_id.country_id.id]),('shipping_range','=','local')],limit=1)
                    if not same_carrier:
                        same_carrier = request.env['delivery.carrier'].sudo().search([('source_country_ids','in',[order.partner_shipping_id.country_id.id]),('shipping_range','=','international')],limit=1)
                        
                for v_cnt in vendor_country_based_group:
                    if v_cnt.country_id.code == order.partner_shipping_id.country_id.code:
                        res_price = getattr(same_carrier, '%s_rate_line_shipment' % same_carrier.delivery_type)(order,vendor_country_based_group[v_cnt])
                        print('==============================error_message=========2===',res_price)
                        if res_price.get('error_message'):
                            is_domestic_vendor_products = True
                            is_domestic_include_error = True
                            vendor_domestic_fees_error = res_price.get("error_message")
                        else:
                            is_domestic_vendor_products = True
                            domestic_vendor_carrier = same_carrier
                            currency = request.env['res.currency'].sudo().search([('name','=',res_price.get('currency_code'))])
                            if currency:
                                if order.currency_id != order.company_id.currency_id:
                                    payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
                            handling_price = (res_price.get('price') *handling_charge)/100
                            price_total = 0.0
                            for s_line in vendor_country_based_group[v_cnt]:
                                price_total += s_line.price_total
                            temp_price = payment_processing_fee + ((transaction_value/100) * (price_total + res_price.get('price') + handling_price))
                            domestic_vendor_price += (temp_price + res_price.get('price'))
                            delivery_price_split = (temp_price + res_price.get('price'))/len(vendor_country_based_group[v_cnt])
                            vendor_country_based_group[v_cnt].write({
                                                                   'delivery_method':same_carrier.id,
                                                                   'delivery_charge':delivery_price_split
                                                                })
                    order.calculate_vendor_lines(order)
        if is_domestic_vendor_products and not is_domestic_include_error:
            delivery_line_track_ids = request.env['delivery.line.track'].sudo().search([
                                                                                        ('country_id','=',order.partner_shipping_id.country_id.id),
                                                                                        ('order_id','=',order.id),
                                                                                        ('is_vendor_track','=',True)
                                                                                        ],limit=1)
            if delivery_line_track_ids:
                delivery_line_track_ids.update({
                                                'is_vendor_track':True,
                                                'delivery_price': domestic_vendor_price
                                                })
            else:
                request.env['delivery.line.track'].sudo().create({
                                                                  'country_id':order.partner_shipping_id.country_id.id,
                                                                  'order_id' : order.id,
                                                                  'carrier_id': domestic_vendor_carrier.id,
                                                                  'delivery_price':domestic_vendor_price,
                                                                  'is_vendor_track':True,
                                                                  })
            res.qcontext.update({'vendor_domestic_fees': round(domestic_vendor_price,2),
                                 'vendor_domestic_fees_error': vendor_domestic_fees_error,
                                 })
            
        if is_domestic_vendor_products and is_domestic_include_error:
            res.qcontext.update({'vendor_domestic_fees': round(domestic_vendor_price,2),
                                 'vendor_domestic_fees_error': vendor_domestic_fees_error,
                                 })
        
        order = request.website.sale_get_order()
        order_delivery_track_lines_vendor_dict = {}
        order_delivery_track_vendor_lines = request.env['delivery.line.track'].search([('order_id','=',order.id),('is_vendor_track','=',True)])
        
        if order_delivery_track_vendor_lines:
            for track_line in order_delivery_track_vendor_lines:
                order_delivery_track_lines_vendor_dict.update({track_line.country_id.code:track_line.carrier_id})
            
            for t_line in order_delivery_track_vendor_lines:
                country_id = t_line.country_id
                for line in order.order_line:
                    stage_ids = request.env['stock.location.route'].sudo().search([('name','=','Dropship')])
                    if not line.location_id and line.product_id.route_ids in stage_ids:
                        vendor = self.get_stock_vendor(order,line)
                        if vendor.country_id == country_id:
                            shipping_lines = line
                            if shipping_lines:
                                shipping_lines.update({'delivery_method':t_line.carrier_id})
        order = request.website.sale_get_order()
        order_delivery_track_lines_vendor_dict = self.prepare_international_shipping_vendor_dict(order,order_delivery_track_lines_vendor_dict)
        
        len_list = len(international_vendor_shipping_methods)
        if len_list:
            for inter_line in international_vendor_shipping_methods:
                if not inter_line in order_delivery_track_lines_vendor_dict:
                    order = request.website.sale_get_order()
                    country_code = inter_line
                    carrier_id = international_vendor_shipping_methods[inter_line][0].id
                    carrier = request.env['delivery.carrier'].sudo().browse(carrier_id)
                    country_id = request.env['res.country'].sudo().search([('code','=',country_code)],limit=1)
                    delivery_price = 0.0
                    res_config = request.env['payment.handling.config'].sudo().search([],limit=1)
                    handling_charge = res_config.handling_charge
                    payment_processing_fee = res_config.payment_processing_fee
                    transaction_value = res_config.transaction_value
                    
                    stage_ids = request.env['stock.location.route'].sudo().search([('name','=','Dropship')])
                    vendor_country_code_group = order.order_line.filtered(lambda n: not n.location_id and n.product_id.route_ids in stage_ids)
                    vendor_country_based_group = {}
                    
                    for v_group in vendor_country_code_group:
                        vendor = self.get_stock_vendor(order,v_group)
                        if vendor in vendor_country_based_group:
                            vendor_country_based_group[vendor] |= v_group
                        else:
                            vendor_country_based_group.update({vendor:v_group})
                            
                    for v_cnt in vendor_country_based_group:
                        if v_cnt.country_id.code == country_code:
                            inside_int_include_error = False
                            
                            res_price = getattr(carrier, '%s_rate_line_shipment' % carrier.delivery_type)(order,vendor_country_based_group[v_cnt])
                            if res_price.get('error_message'):
                                inside_int_include_error = res_price.get('error_message')
                                is_international_include_error = True
                                print('==============================error_message=========1===',res_price)
                                res_price.get("error_message")
                            else:
                                currency = request.env['res.currency'].sudo().search([('name','=',res_price.get('currency_code'))])
                                if currency:
                                    if order.currency_id != order.company_id.currency_id:
                                        payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
                                handling_price = (res_price.get('price') *handling_charge)/100
                                price_total = 0.0
                                for s_line in vendor_country_based_group[v_cnt]:
                                    price_total += s_line.price_total
                                temp_price = payment_processing_fee + ((transaction_value/100) * (price_total + res_price.get('price') + handling_price))
                                delivery_price += (temp_price + res_price.get('price'))
                                delivery_price_split = (temp_price + res_price.get('price'))/len(vendor_country_based_group[v_cnt])
                                vendor_country_based_group[v_cnt].write({
                                                                       'delivery_method':carrier.id,
                                                                       'delivery_charge':delivery_price_split
                                                                    })
                                order.calculate_vendor_lines(order)
                        delivery_line_track_ids = request.env['delivery.line.track'].sudo().search([
                                                                                                    ('country_id','=',country_id.id),
                                                                                                    ('order_id','=',order.id),
                                                                                                    ('is_vendor_track','=',True)
                                                                                                    ],limit=1)
#                     if not is_inside_int_include_error:
                    if delivery_line_track_ids:
                        delivery_line_track_ids.update({
                                                        'carrier_id':carrier.id,
                                                        'delivery_price': delivery_price,
                                                        'is_vendor_track':True
                                                        })
                    else:
                        request.env['delivery.line.track'].sudo().create({
                                                                          'country_id':country_id.id,
                                                                          'order_id' : order.id,
                                                                          'carrier_id': carrier.id,
                                                                          'delivery_price':delivery_price,
                                                                          'is_vendor_track':True
                                                                          })
                    track_id = request.env['delivery.line.track'].sudo().search([
                                                                            ('country_id.code','=',inter_line),
                                                                            ('order_id','=',order.id),
                                                                            ('is_vendor_track','=',True)
                                                                            ],limit=1)
                    
                    if track_id:
                        order_delivery_track_lines_vendor_dict.update({
                                                                    inter_line:[carrier,track_id.delivery_price]
                                                                    })
                    else:
                        order_delivery_track_lines_vendor_dict.update({
                                                                    inter_line:[carrier,False]
                                                                    })
        
        res.qcontext.update({
                             'is_domestic_vendor_products':is_domestic_vendor_products,
                             'international_vendor_shipping_methods':international_vendor_shipping_methods,
                             'order_delivery_track_lines_vendor_dict':order_delivery_track_lines_vendor_dict,
#                              'is_international_include_error':is_international_include_error,
#                              'inside_int_include_error':inside_int_include_error,
                             
                             })  
        order = request.website.sale_get_order()
        order._compute_website_order_line()
        order.recalculate_vendor_lines(order)
        order.check_blank_vendor_delivery_lines()
        
        return res
    
    #=========all line group price calculate=================
    @http.route(['/my/calculate/vendor/international_shipping'], type='json', auth="public", website=True)
    def my_calculate_vendor_international_shipping(self,**post):
        order = request.website.sale_get_order()
        country_code = post.get('vendor_country_codei')
        carrier_id = int(post.get('vendor_delivery_idi'))
        carrier = request.env['delivery.carrier'].sudo().browse(carrier_id)
        delivery_price = 0.0
        res_config = request.env['payment.handling.config'].sudo().search([],limit=1)
        handling_charge = res_config.handling_charge
        payment_processing_fee = res_config.payment_processing_fee
        transaction_value = res_config.transaction_value
        stage_ids = request.env['stock.location.route'].sudo().search([('name','=','Dropship')])
        vendor_country_code_group = order.order_line.filtered(lambda n: not n.location_id and n.product_id.route_ids in stage_ids)
        vendor_country_based_group = {}
#         is_error = False
        for v_group in vendor_country_code_group:
            vendor = self.get_stock_vendor(order,v_group)
            if vendor.country_id.code == country_code:
                if vendor in vendor_country_based_group:
                    vendor_country_based_group[vendor] |= v_group
                else:
                    vendor_country_based_group.update({vendor:v_group})
        for v_cnt in vendor_country_based_group:
            if v_cnt.country_id.code == country_code:
                res = getattr(carrier, '%s_rate_line_shipment' % carrier.delivery_type)(order,vendor_country_based_group[v_cnt])
                if res.get('error_message'):
                    print('==============================error_message=========3===',res)
                    return res
                else:
                    currency = request.env['res.currency'].sudo().search([('name','=',res.get('currency_code'))])
                    if currency:
                        if order.currency_id != order.company_id.currency_id:
                            payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
                    handling_price = (res.get('price') *handling_charge)/100
                    price_total = 0.0
                    for s_line in vendor_country_based_group[v_cnt]:
                        price_total += s_line.price_total
                    temp_price = payment_processing_fee + ((transaction_value/100) * (price_total + res.get('price') + handling_price))
                    delivery_price += (temp_price + res.get('price'))
        
        return {'vendor_delivery_pricei': order.currency_id.symbol + ' ' + str(round(delivery_price,2))}
    
    
    #=========line group price calculate=================
    @http.route(['/calculate/vendor/international_shipping'], type='json', auth="public", website=True)
    def calculate_vendor_international_shipping(self,**post):
        order = request.website.sale_get_order()
        country_code = post.get('vendor_country_code')
        carrier_id = int(post.get('vendor_delivery_id'))
        carrier = request.env['delivery.carrier'].sudo().browse(carrier_id)
        country_id = request.env['res.country'].sudo().search([('code','=',country_code)],limit=1)
        delivery_price = 0.0
        res_config = request.env['payment.handling.config'].sudo().search([],limit=1)
        handling_charge = res_config.handling_charge
        payment_processing_fee = res_config.payment_processing_fee
        transaction_value = res_config.transaction_value
        value = {}
        stage_ids = request.env['stock.location.route'].sudo().search([('name','=','Dropship')])
        vendor_country_code_group = order.order_line.filtered(lambda n: not n.location_id and n.product_id.route_ids in stage_ids)
        vendor_country_based_group = {}
        
        for v_group in vendor_country_code_group:
            vendor = self.get_stock_vendor(order,v_group)
            if vendor.country_id.code == country_code:
                if vendor in vendor_country_based_group:
                    vendor_country_based_group[vendor] |= v_group
                else:
                    vendor_country_based_group.update({vendor:v_group})
                
        for v_cnt in vendor_country_based_group:
            if v_cnt.country_id.code == country_code:
                res = getattr(carrier, '%s_rate_line_shipment' % carrier.delivery_type)(order,vendor_country_based_group[v_cnt])
                if res.get('error_message'):
                    print('==============================error_message=========4===',res)
                    vendor_country_based_group[v_cnt].write({
                                                           'delivery_method':carrier.id,
                                                           'delivery_charge':0.0
                                                        })
                    order.calculate_vendor_lines(order)
                    order = request.website.sale_get_order()
                    order._compute_website_order_line()
                    return res
                else:
                    currency = request.env['res.currency'].sudo().search([('name','=',res.get('currency_code'))])
                    if currency:
                        if order.currency_id != order.company_id.currency_id:
                            payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
                    handling_price = (res.get('price') *handling_charge)/100
                    price_total = 0.0
                    for s_line in vendor_country_based_group[v_cnt]:
                        price_total += s_line.price_total
                    temp_price = payment_processing_fee + ((transaction_value/100) * (price_total + res.get('price') + handling_price))
                    delivery_price += (temp_price + res.get('price'))
                    delivery_price_split = (temp_price + res.get('price'))/len(vendor_country_based_group[v_cnt])
                    vendor_country_based_group[v_cnt].write({
                                                           'delivery_method':carrier.id,
                                                           'delivery_charge':delivery_price_split
                                                        })
                    order.calculate_vendor_lines(order)

        delivery_line_track_ids = request.env['delivery.line.track'].sudo().search([
                                                                                    ('country_id','=',country_id.id),
                                                                                    ('order_id','=',order.id),
                                                                                    ('is_vendor_track','=',True)
                                                                                    ],limit=1)
        if delivery_line_track_ids:
            delivery_line_track_ids.update({
                                            'carrier_id':carrier.id,
                                            'delivery_price': delivery_price,
                                            'is_vendor_track':True
                                            })
        else:
            request.env['delivery.line.track'].sudo().create({
                                                              'country_id':country_id.id,
                                                              'order_id' : order.id,
                                                              'carrier_id': carrier.id,
                                                              'delivery_price':delivery_price,
                                                              'is_vendor_track':True
                                                              })
                
        order = request.website.sale_get_order()
        order._compute_website_order_line()

        value['website_sale.cart_summary'] = request.env['ir.ui.view'].render_template("website_sale.cart_summary",{'website_sale_order':order})
        value['vendor_amount_delivery'] = order.currency_id.symbol + ' ' + str(order.vendor_amount_delivery)
        return value
    