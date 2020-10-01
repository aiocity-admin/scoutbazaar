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
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import pdf
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError, UserError

class StockLocation(models.Model):
    
    _inherit = 'stock.location'
    
    state_id = fields.Many2one('res.country.state',string='State',domain="[('country_id.code','=','PH')]")
    nso_location_id = fields.Many2one('res.partner', string="NSO Location",domain="[('is_nso','=',True)]")
    state_country_code = fields.Char(related='nso_location_id.country_id.code')

class JTDeliveryCarrier(models.Model):
    
    _inherit = 'delivery.carrier'
    
    country_id = fields.Many2one('res.country','Country')
    
    delivery_code = fields.Char(string = 'Delivery Code')
    
    country_code = fields.Char(string='Country Code',related='country_id.code')
    
    delivery_type = fields.Selection(selection_add=[('base_on_jt_configuration', 'GSR')])
    
    big_size_price = fields.Float('Big Product Box Price')
    
    # get rate======================================
    @api.onchange('delivery_type')
    def onchange_delivery_type(self):
        if self.delivery_type:
            self.integration_level = 'rate'
    
    # Get vendor======================================
    def get_stock_vendor_jt(self,order,line):
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
            
            
    
    def get_maximum_shipping_rate(self,origin_id,destination_id,total_weight_remaining):
        shipping_rates = self.env['jt.shipping.rates'].sudo().search([
                                                                        ('origin_id','=',origin_id.id),
                                                                        ('state_id','=',destination_id.id),
                                                                        ])
        
#         if not shipping_rates:
#             shipping_rates = self.env['jt.shipping.rates'].sudo().search([
#                                                                         ('origin_id','=',origin_id.id),
#                                                                         ('state_id','=',destination_id.id),
#                                                                         ('min_weight','<',total_weight_remaining),
#                                                                         ('max_weight','>=',total_weight_remaining),
#                                                                         ])
        
        shipping_rate_list = []
        shipping_rate_list2 = []
        shipping_need_max = True
        max_rate = 0.0
        max_shipping_rate = False
        for rates in shipping_rates:
            if rates.max_weight <= total_weight_remaining:
                shipping_rate_list.append(rates.max_weight)
            elif rates.max_weight >= total_weight_remaining:
                shipping_need_max = False
            
        if len(shipping_rate_list) > 0 and shipping_need_max:
            max_rate = max(shipping_rate_list)
            max_rate_record = self.env['jt.shipping.rates'].sudo().search([
                                                                        ('origin_id','=',origin_id.id),
                                                                        ('state_id','=',destination_id.id),
                                                                        ('max_weight','=',max_rate)
                                                                       ])
            if max_rate_record:
                max_rate = max_rate_record.rate
        
        else:
            shipping_rates_2 = self.env['jt.shipping.rates'].sudo().search([
                                                                          ('origin_id','=',origin_id.id),
                                                                          ('state_id','=',destination_id.id),
                                                                          ('min_weight','<=',total_weight_remaining),
                                                                          ('max_weight','>=',total_weight_remaining)
                                                                          ])
            if shipping_rates_2:
                for rate2 in shipping_rates_2:
                    shipping_rate_list2.append(rate2.max_weight)
                
                if len(shipping_rates_2) > 0:
                    max_rate = max(shipping_rate_list2)
                    
                    max_rate_record = self.env['jt.shipping.rates'].sudo().search([
                                                                        ('origin_id','=',origin_id.id),
                                                                        ('state_id','=',destination_id.id),
                                                                        ('max_weight','=',max_rate)
                                                                       ])
                    if max_rate_record:
                        max_rate = max_rate_record.rate
                    
                    
        if max_rate > 0:
            max_shipping_rate = self.env['jt.shipping.rates'].sudo().search([
                                                                        ('origin_id','=',origin_id.id),
                                                                        ('state_id','=',destination_id.id),
                                                                        ('rate','=',max_rate)
                                                                       ])
            if max_shipping_rate:
                    total_weight_remain = total_weight_remaining - max_shipping_rate.max_weight
                    rate = max_shipping_rate.rate
                    return {'rate':rate,'remain':total_weight_remain}
            else:
                return False
    
    def _get_jt_price_available(self,order,lines):
        self.ensure_one()
        destination_id = order.partner_shipping_id.state_id
        origin_id = False
        total_weight = 0.0
        total_weight_remain = 0.0
        big_product_count =0.0
        total_delivery_cost = 0.0
        total_rate =0.0
        big_product_price = order.carrier_id.big_size_price
        for line in lines:
            stage_ids = self.env['stock.location.route'].sudo().search([('name','=','Dropship')])
            if not line.location_id and line.product_id.route_ids in stage_ids:
                vendor = self.get_stock_vendor_jt(order,line)
                if vendor:
                    if vendor.country_id != order.partner_shipping_id.country_id:
                        return False
                    else:
                        origin_id = vendor.state_id
            else:
                if line.location_id.state_id:
                    if line.location_id.nso_location_id.country_id != order.partner_shipping_id.country_id:
                        return False
                    else:
                        origin_id = line.location_id.state_id
                else:
                    return False
            total_weight += (line.product_id.weight * line.product_uom_qty)
            
            if line.product_id.is_big_size:
                big_product_count += (line.product_uom_qty * 1)
        if origin_id and destination_id:
            total_weight_remain = total_weight
            shipping_rates = self.env['jt.shipping.rates'].sudo().search([
                                                                          ('origin_id','=',origin_id.id),
                                                                          ('state_id','=',destination_id.id),
                                                                          ('min_weight','<',total_weight),
                                                                          ('max_weight','>=',total_weight),
                                                                          ],limit=1)
            if shipping_rates:
                total_delivery_cost += shipping_rates.rate
                
            elif total_weight_remain > 0:
                while total_weight_remain > 0:
                    data = self.get_maximum_shipping_rate(origin_id,destination_id,total_weight_remain)
                    if data:
                        if data['remain']:
                            total_weight_remain = data['remain']
                        if data['rate']:
                            total_delivery_cost += data['rate']
                    else:
                        return False
                    
            if big_product_count > 0:
                total_delivery_cost += (big_product_count * big_product_price)
        return total_delivery_cost
    
    def base_on_jt_configuration_rate_line_shipment(self, order, lines):
        carrier = self._match_address(order.partner_shipping_id)
        currency = self.env['res.currency'].sudo().search([('name','=','PHP')])
        if not carrier:
            return {'success': False,
                    'price': 0.0,
                    'error_message': _('Error: no matching grid.'),
                    'warning_message': False}

        try:
            price_unit = self._get_jt_price_available(order,lines)
            if not price_unit:
                return {'success': False,
                    'price': 0.0,
                    'error_message': 'JT Express does not support shipping service in selected area!',
                    'warning_message': False}
        except UserError as e:
            return {'success': False,
                    'price': 0.0,
                    'error_message': 'JT Express does not support shipping service in selected area!',
                    'warning_message': False}
        price_unit = currency._convert(price_unit,order.currency_id,order.company_id,fields.Date.today())
#         if order.company_id.currency_id.id != order.pricelist_id.currency_id.id:
#             price_unit = order.company_id.currency_id.with_context(date=order.date_order).compute(price_unit, order.pricelist_id.currency_id)
        return {'success': True,
                'price': price_unit,
                'error_message': False,
                'warning_message': False,
                'currency_code':'PHP'}