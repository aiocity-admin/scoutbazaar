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

from odoo import api, fields, models, _
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, UserError

class VendorSaleOrderLine(models.Model):
    
    _inherit='sale.order.line'
    
    is_vendor_delivery_line = fields.Boolean(string="Is a Vendor Line?")

class VendorUsers(models.Model):
    
    _inherit='product.template'
    
    vendor_user_product = fields.Many2one('res.users',string='Vendor User', default=lambda self: self.env.user)
    vendor_user_partner_id = fields.Many2one('res.partner',related="vendor_user_product.partner_id")
    international_ids = fields.Many2many('res.partner',string="International locations") 
    is_vendor_product = fields.Boolean('Is Vendor Product')

    @api.model_create_multi
    def create(self,vals_list):
        res = super(VendorUsers, self).create(vals_list)
        if 'vendor_user_product' in vals_list[0]:
            user_id = self.env['res.users'].sudo().browse(vals_list[0]['vendor_user_product'])
            if user_id:
                has_group = user_id.has_group('scout_vendor.group_vendor_product')
                if has_group:
                    rule_location = self.env['stock.location.route'].sudo()
                    for i in res.route_ids:
                        stage_ids = rule_location.search([('name','=','Dropship')])
                        if stage_ids:
                            res.write({'route_ids':[(6,0,stage_ids.ids)]})
        return res
    
    # @api.multi
    # def write(self,vals):
    #     res = super(VendorUsers,self).write(vals)
    #     user_id = self.env['res.users'].has_group('scout_vendor.group_vendor_product')
    #     if user_id:
    #         rule_location = self.env['stock.location.route'].sudo()
    #         for i in res.route_ids:
    #             stage_ids = rule_location.search([('name','=','Dropship')])
    #             if stage_ids:
    #                 res.write({'route_ids':[(6,0,stage_ids.ids)]})
    #     return res
    
class VendorSaleOrder(models.Model):
     
    _inherit='sale.order'
    
    vendor_amount_delivery = fields.Monetary(
        compute='_compute_vendor_amount_delivery', digits=0,
        string='Vendor Delivery Amount',
        help="The amount without tax.", store=True, track_visibility='always')
    
    
    @api.depends('order_line.price_unit', 'order_line.tax_id', 'order_line.discount', 'order_line.product_uom_qty')
    def _compute_vendor_amount_delivery(self):
        for order in self:
            if self.env.user.has_group('account.group_show_line_subtotals_tax_excluded'):
                order.vendor_amount_delivery = sum(order.order_line.filtered('is_vendor_delivery_line').mapped('price_subtotal'))
            else:
                order.vendor_amount_delivery = sum(order.order_line.filtered('is_vendor_delivery_line').mapped('price_total'))
    
    # User in Vendor mail Send ==================
    @api.multi
    def action_confirm(self):
        res = super(VendorSaleOrder, self).action_confirm()
        vendor_list = []
        for line in self.order_line:
            rule_location = self.env['stock.location.route'].sudo().search([('name','=','Dropship')])
            if line.product_id.route_ids in rule_location:
                if not line.product_id.vendor_user_product.id  in vendor_list:
                    vendor_list.append(line.product_id.vendor_user_product.id)
        for vendor_user in vendor_list:
            if vendor_user:
                vendor = self.env['res.users'].sudo().search([('id','=',int(vendor_user))])
                template_id = self.env.ref('scout_vendor.mail_template_sale_order_line_dropship',False)
                if template_id:
                    template_id.sudo().write({
                        'email_to': str(vendor.email),
                        'email_from': template_id.email_from
                    })
                    ups_list =  {'03': 'UPS Ground',
                                            '11': 'UPS Standard',
                                            '01': 'UPS Next Day',
                                            '14': 'UPS Next Day AM',
                                            '13': 'UPS Next Day Air Saver',
                                            '02': 'UPS 2nd Day',
                                            '59': 'UPS 2nd Day AM',
                                            '12': 'UPS 3-day Select',
                                            '65': 'UPS Saver',
                                            '07': 'UPS Worldwide Express',
                                            '08': 'UPS Worldwide Expedited',
                                            '54': 'UPS Worldwide Express Plus',
                                            '96': 'UPS Worldwide Express Freight'}
                    mail_id = template_id.with_context({'ups_list':ups_list,'vendor_name':vendor.name}).send_mail(self.id, force_send=True, raise_exception=False)
        return res
    
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

    def calculate_vendor_lines(self,order):
        sale_order_line_obj = self.env['sale.order.line'].sudo()
        delivery_product = self.env.ref('delivery.product_product_delivery').sudo()
        delivery_charge = 0.0
        for line in order.order_line:
            stage_ids = self.env['stock.location.route'].sudo().search([('name','=','Dropship')])
            if not line.location_id and line.product_id.route_ids in stage_ids:
                delivery_charge += line.delivery_charge
        delivery_line = order.order_line.filtered(lambda r: r.name == "Total Shipping and Handling Charges(Dropshipper)")
        if delivery_line:
            delivery_line.write({'price_unit':delivery_charge})
        else:
            vals = {
                    'order_id':order.id,
                    'name':'Total Shipping and Handling Charges(Dropshipper)',
                    'product_id':delivery_product.id,
                    'product_uom': delivery_product.sudo().uom_id.id,
                    'price_unit':delivery_charge,
                    'product_uom_qty':1.0,
                    'is_vendor_delivery_line':True
                    }
            if delivery_charge > 0:
                sale_order_line_obj.create(vals)
    
    def recalculate_vendor_lines(self,order):
        vendor_delivery_lines = order.order_line.filtered(lambda r:r.is_vendor_delivery_line)
        vendor_delivery_lines.update({'delivery_charge':0.0})
        res_config = self.env['payment.handling.config'].sudo().search([],limit=1)
        handling_charge = res_config.handling_charge
        payment_processing_fee = res_config.payment_processing_fee
        transaction_value = res_config.transaction_value
        
        stage_ids = self.env['stock.location.route'].sudo().search([('name','=','Dropship')])
        vendor_country_code_group = order.order_line.filtered(lambda n: not n.location_id and n.product_id.route_ids in stage_ids)
        vendor_same_country_based_group = {}
        vendor_diff_country_based_group = {}
        
        for v_group in vendor_country_code_group:
            vendor = self.get_stock_vendor(order,v_group)
            if vendor.country_id == order.partner_shipping_id.country_id:
                if vendor in vendor_same_country_based_group:
                    vendor_same_country_based_group[vendor] |= v_group
                else:
                    vendor_same_country_based_group.update({vendor:v_group})
            else:
                if vendor in vendor_diff_country_based_group:
                    vendor_diff_country_based_group[vendor] |= v_group
                else:
                    vendor_diff_country_based_group.update({vendor:v_group})
                    
                    
        
        #Same Source destination code==================================
        same_carrier = False
        same_delivery_price = 0.0
        
        if vendor_same_country_based_group:
            same_carrier = self.env['delivery.carrier'].sudo().search([('source_country_ids','in',[order.partner_shipping_id.country_id.id]),('shipping_range','=','local')],limit=1)
            if not same_carrier:
                same_carrier = self.env['delivery.carrier'].sudo().search([('source_country_ids','in',[order.partner_shipping_id.country_id.id]),('shipping_range','=','international')],limit=1)
        
        for v_cnt in vendor_same_country_based_group:
            if v_cnt.country_id.code == order.partner_shipping_id.country_id.code:
                res_price = getattr(same_carrier, '%s_rate_line_shipment' % same_carrier.delivery_type)(order,vendor_same_country_based_group[v_cnt])
                if res_price.get('error_message'):
                    res_price.get("error_message")
                    vendor_same_country_based_group[v_cnt].write({
                                                           'delivery_method':same_carrier.id,
                                                           'delivery_charge':0.0,
                                                           'shipping_charge':0.0,
                                                           'extra_charge_product':0.0,
                                                        })
                    order.calculate_vendor_lines(order)
                else:
                    currency = self.env['res.currency'].sudo().search([('name','=',res_price.get('currency_code'))])
                    if currency:
                        if order.currency_id != order.company_id.currency_id:
                            payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
                    handling_price = (res_price.get('price') *handling_charge)/100
                    price_total = 0.0
                    for s_line in vendor_same_country_based_group[v_cnt]:
                        price_total += s_line.price_total
                    temp_price = payment_processing_fee + ((transaction_value/100) * (price_total + res_price.get('price') + handling_price))
                    same_delivery_price += (temp_price + res_price.get('price'))
                    delivery_price_split = (temp_price + res_price.get('price'))/len(vendor_same_country_based_group[v_cnt])
                    shipping_price_split = res_price.get('price')/len(vendor_same_country_based_group[v_cnt])
                    extra_charge_split = temp_price/len(vendor_same_country_based_group[v_cnt])
                    vendor_same_country_based_group[v_cnt].write({
                                                           'delivery_method':same_carrier.id,
                                                           'delivery_charge':delivery_price_split,
                                                           'shipping_charge':shipping_price_split,
                                                           'extra_charge_product':extra_charge_split,
                                                        })
                    order.calculate_vendor_lines(order)
        
        if same_carrier:
            delivery_line_track_ids = self.env['delivery.line.track'].sudo().search([
                                                                            ('country_id','=',order.partner_shipping_id.country_id.id),
                                                                            ('order_id','=',order.id),
                                                                            ('is_vendor_track','=',True)
                                                                            ],limit=1)
            if delivery_line_track_ids:
                delivery_line_track_ids.update({
                                                'carrier_id':same_carrier.id,
                                                'delivery_price': round(same_delivery_price,2),
                                                'is_vendor_track':True
                                                })
            else:
                self.env['delivery.line.track'].sudo().create({
                                                                  'country_id':order.partner_shipping_id.country_id.id,
                                                                  'order_id' : order.id,
                                                                  'carrier_id': same_carrier.id,
                                                                  'delivery_price':round(same_delivery_price,2),
                                                                  'is_vendor_track':True
                                                                  })
                
        #Different Source Destination Code====================
        for v_diff_cnt in vendor_diff_country_based_group:
            carrier = vendor_diff_country_based_group[v_diff_cnt][0].delivery_method
            country_id = v_diff_cnt.country_id.id
            if not carrier:
                carrier = self.env['delivery.carrier'].sudo().search([('source_country_ids','in',[country_id]),('shipping_range','=','international')],limit=1)
            delivery_price = 0.0
            if carrier:
                res_price = getattr(carrier, '%s_rate_line_shipment' % carrier.delivery_type)(order,vendor_diff_country_based_group[v_diff_cnt])
                if res_price.get('error_message'):
                    res_price.get("error_message")
                    vendor_diff_country_based_group[v_diff_cnt].write({
                                                           'delivery_method':carrier.id,
                                                           'delivery_charge':0.0,
                                                           'shipping_charge':0.0,
                                                           'extra_charge_product':0.0,
                                                        })
                    order.calculate_vendor_lines(order)
                else:
                    currency = self.env['res.currency'].sudo().search([('name','=',res_price.get('currency_code'))])
                    if currency:
                        if order.currency_id != order.company_id.currency_id:
                            payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
                    handling_price = (res_price.get('price') *handling_charge)/100
                    price_total = 0.0
                    for s_line in vendor_diff_country_based_group[v_diff_cnt]:
                        price_total += s_line.price_total
                    temp_price = payment_processing_fee + ((transaction_value/100) * (price_total + res_price.get('price') + handling_price))
                    delivery_price += (temp_price + res_price.get('price'))
                    delivery_price_split = (temp_price + res_price.get('price'))/len(vendor_diff_country_based_group[v_diff_cnt])
                    shipping_price_split = res_price.get('price')/len(vendor_diff_country_based_group[v_diff_cnt])
                    extra_charge_split = temp_price/len(vendor_diff_country_based_group[v_diff_cnt])
                    vendor_diff_country_based_group[v_diff_cnt].write({
                                                           'delivery_method':carrier.id,
                                                           'delivery_charge':delivery_price_split,
                                                           'shipping_charge':shipping_price_split,
                                                           'extra_charge_product':extra_charge_split,
                                                        })
                    order.calculate_vendor_lines(order)
                    
                delivery_line_track_ids = self.env['delivery.line.track'].sudo().search([
                                                                            ('country_id','=',country_id),
                                                                            ('order_id','=',order.id),
                                                                            ('is_vendor_track','=',True)
                                                                            ],limit=1)
                if delivery_line_track_ids:
                    delivery_line_track_ids.update({
                                                    'carrier_id':carrier.id,
                                                    'delivery_price': round(delivery_price,2),
                                                    'is_vendor_track':True
                                                    })
                else:
                    self.env['delivery.line.track'].sudo().create({
                                                                      'country_id':country_id,
                                                                      'order_id' : order.id,
                                                                      'carrier_id': carrier.id,
                                                                      'delivery_price':round(delivery_price,2),
                                                                      'is_vendor_track':True
                                                                      })
                
    def check_blank_vendor_delivery_lines(self): 
        for line in self.order_line:
            if line.is_vendor_delivery_line and line.delivery_charge <= 0:
                line.unlink()
                self.recalculate_vendor_lines(self)
    
class VendorUsersLogin(models.Model):

    _inherit='res.users'

    @api.multi
    def _is_vender_users(self):
        self.ensure_one()
        return self.has_group('scout_vendor.group_vendor_product')
