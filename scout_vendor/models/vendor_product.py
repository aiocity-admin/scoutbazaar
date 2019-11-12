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
            if line.route_id == rule_location:
                if not line.product_id.vendor_user_product.id  in vendor_list:
                    vendor_list.append(line.product_id.vendor_user_product.id)
        for vendor_user in vendor_list:
            if vendor_user:
                vendor = self.env['res.users'].sudo().search([('id','=',int(vendor_user))])
                template_id = self.env.ref('scout_vendor.mail_template_sale_order_line_dropship',False)
                if template_id:
                    template_id.sudo().write({
                        'email_to': str(vendor.email),
                        'email_from': self.env.user.company_id.email  
                    })
                    mail_id = template_id.with_context({'vendor_name':vendor.name}).send_mail(self.id, force_send=True, raise_exception=False)
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
        
        for line in order.order_line:
            stage_ids = self.env['stock.location.route'].sudo().search([('name','=','Dropship')])
            if not line.location_id and line.product_id.route_ids in stage_ids:
                vendor = self.get_stock_vendor(order,line)
                if vendor:
                    if vendor.country_id == order.partner_shipping_id.country_id:
                        delivery_carrier = self.env['delivery.carrier'].sudo().search([('source_country_ids','in',[order.partner_shipping_id.country_id.id]),('shipping_range','=','local')],limit=1)
                        if not delivery_carrier:
                            delivery_carrier = self.env['delivery.carrier'].sudo().search([('source_country_ids','in',[order.partner_shipping_id.country_id.id]),('shipping_range','=','international')],limit=1)
                        if delivery_carrier:
                            res_price = getattr(delivery_carrier, '%s_rate_line_shipment' % delivery_carrier.delivery_type)(order,line)
                            if not res_price.get('error_message'):
                                currency = self.env['res.currency'].sudo().search([('name','=',res_price.get('currency_code'))])
                                if currency:
                                    if order.currency_id != order.company_id.currency_id:
                                        payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
                                handling_price = (res_price.get('price') *handling_charge)/100
                                temp_price = payment_processing_fee + ((transaction_value/100) * (line.price_total + res_price.get('price') + handling_price))
                                line.write({
                                            'delivery_method':delivery_carrier.id,
                                            'delivery_charge':res_price.get('price') + temp_price
                                            })
                                order.calculate_vendor_lines(order)
                    else:
                        country_code = vendor.country_id.code
                        carrier = line.delivery_method if line.delivery_method else False
                        country_id = vendor.country_id
                        delivery_price = 0.0
                        lines_to_change = {}
                        if carrier:
                            for so_line in order.order_line:
                                stage_ids = self.env['stock.location.route'].sudo().search([('name','=','Dropship')])
                                if not so_line.location_id and so_line.product_id.route_ids in stage_ids:
                                    vendor = self.get_stock_vendor(order,so_line)
                                    if vendor:
                                        if vendor.country_id.code == country_code:
                                            res = getattr(carrier, '%s_rate_line_shipment' % carrier.delivery_type)(order,so_line)
                                            if res.get('error_message'):
                                                return res.get("error_message")
                                            else:
                                                currency = self.env['res.currency'].sudo().search([('name','=',res.get('currency_code'))])
                                                if currency:
                                                    if order.currency_id != order.company_id.currency_id:
                                                        payment_processing_fee = currency._convert(payment_processing_fee,order.currency_id,order.company_id,fields.Date.today())
                                                handling_price = (res.get('price') *handling_charge)/100
                                                temp_price = payment_processing_fee + ((transaction_value/100) * (so_line.price_total + res.get('price') + handling_price))
                                                lines_to_change.update({so_line:res.get('price') + temp_price})
                                                delivery_price += (res.get('price') + temp_price)
                            if lines_to_change:
                                for change_line in lines_to_change:
                                    line_id = self.env['sale.order.line'].sudo().browse(change_line.id)
                                    if line_id:
                                        line_id.write({
                                                        'delivery_method':carrier.id,
                                                        'delivery_charge':lines_to_change[change_line]
                                                        })
                                        order.calculate_vendor_lines(order)
                                delivery_line_track_ids = self.env['delivery.line.track'].sudo().search([
                                                                                                            ('country_id','=',country_id.id),
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
                                                                                      'country_id':country_id.id,
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
