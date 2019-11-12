from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import pdf
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.addons.delivery_ups.models.ups_request import UPSRequest, Package

class SaleOrderLine(models.Model):
    
    _inherit='sale.order.line'
    
    location_id = fields.Many2one("stock.location", string="Location")
    delivery_charge = fields.Float(string="Delivery Charge")
    delivery_method = fields.Many2one("delivery.carrier", string="Delivery Method")
    line_delivery_message = fields.Char(readonly=True, copy=False)
    is_nso_delivery_line = fields.Boolean(string="Is a NSO Line?")
    
    def send_sale_order_email(self,order,line_list):
        for location_id in line_list:
            if location_id:
                location = self.env['stock.location'].sudo().search([('id','=',int(location_id))])
                partner = location.nso_location_id
                if partner:
                    template_id = self.env.ref('scout_stock.email_template_edi_sale_line', False)
                    if template_id:
                        template_id.sudo().write({
                          'email_to': str(partner.email),
                          'email_from': template_id.email_from,
                        })
                        a = template_id.with_context({'location_id':location_id,'name':location.name}).send_mail(order.id, force_send=True, raise_exception=False)
    
    @api.multi
    def _action_launch_stock_rule(self):
        """
        Launch procurement group run method with required/custom fields genrated by a
        sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        errors = []
        for line in self:
            if line.state != 'sale' or not line.product_id.type in ('consu','product'):
                continue
            qty = line._get_qty_procurement()
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue

            group_id = line.order_id.procurement_group_id
            if not group_id:
                group_id = self.env['procurement.group'].create({
                    'name': line.order_id.name, 'move_type': line.order_id.picking_policy,
                    'sale_id': line.order_id.id,
                    'partner_id': line.order_id.partner_shipping_id.id,
                })
                line.order_id.procurement_group_id = group_id
            else:
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_uom_qty - qty

            procurement_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            if procurement_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                product_qty = line.product_uom._compute_quantity(product_qty, quant_uom, rounding_method='HALF-UP')
                procurement_uom = quant_uom

            try:
                self.env['procurement.group'].with_context(src_loc=line.location_id).run(line.product_id, product_qty, procurement_uom, line.order_id.partner_shipping_id.property_stock_customer, line.name, line.order_id.name, values)
            except UserError as error:
                errors.append(error.name)
        if errors:
            raise UserError('\n'.join(errors))
        return True
    
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    nso_amount_delivery = fields.Monetary(
        compute='_compute_nso_amount_delivery', digits=0,
        string='NSO Delivery Amount',
        help="The amount without tax.", store=True, track_visibility='always')
    
    
    @api.depends('order_line.price_unit', 'order_line.tax_id', 'order_line.discount', 'order_line.product_uom_qty')
    def _compute_nso_amount_delivery(self):
        for order in self:
            if self.env.user.has_group('account.group_show_line_subtotals_tax_excluded'):
                order.nso_amount_delivery = sum(order.order_line.filtered('is_nso_delivery_line').mapped('price_subtotal'))
            else:
                order.nso_amount_delivery = sum(order.order_line.filtered('is_nso_delivery_line').mapped('price_total'))
    
    @api.one
    def _compute_website_order_line(self):
        super(SaleOrder, self)._compute_website_order_line()
        self.website_order_line = self.website_order_line.filtered(lambda l: not l.is_delivery and not l.is_nso_delivery_line and not l.is_vendor_delivery_line)
    
    def get_country_by_code(self,code):
        
        country = self.env['res.country'].sudo().search([('code','=',code)],limit=1)
        if country:
            return country.name
        else:
            return ''
    
#     def _check_order_line_carrier(self, order):
#         self.ensure_one()
#         carrier = False
#         DeliveryCarrier = self.env['delivery.carrier']
#         for line in order.order_line:
#             if line.location_id:
#                 if not line.product_id.type == 'service':
#                     
#                     if order.partner_shipping_id.country_id.code == line.location_id.nso_location_id.country_id.code:
#                         if order.partner_shipping_id.country_id.code == 'PH':
#                             line.delivery_method = False
#                             carrier = self.env['delivery.carrier'].sudo().search([('delivery_type','=','base_on_jt_configuration')],limit=1)
#                             line.delivery_method = carrier.id
#                             line.delivery_charge = False
#         #                     price_jt = line.delivery_method._get_jt_order_line_price(order,line)
#                             price_jt = line.delivery_method.base_on_jt_configuration_rate_shipment(order,line)
#                             if price_jt['success']:
#                                 line.delivery_charge = price_jt['price']
#                                 line.line_delivery_message = price_jt['warning_message']
#                             else:
#                                 line.delivery_price = 0.0
#                                 line.line_delivery_message = price_jt['error_message']
#                         
# #                         elif order.partner_shipping_id.country_id.code == 'HK':
# #                             line.delivery_method = False
# #                             carrier = self.env['delivery.carrier'].sudo().search([('name','=','j&T Express')],limit=1)
# #                             line.delivery_method = carrier.id
#                     else:
#                         line.delivery_method = False
#                         carrier = self.env['delivery.carrier'].sudo().search([('name','=','UPS International'),('source_country_ids','in',[line.location_id.nso_location_id.country_id.id])],limit=1)
#                         line.delivery_method = carrier.id
#                         line.delivery_charge = False
#                         res = line.delivery_method.ups_rate_line_shipment(order,line)
#                         if res['success']:
#                             line.delivery_charge = res['price']
#                             line.line_delivery_message = res['warning_message']
#                         else:
#                             line.delivery_price = 0.0
#                             line.line_delivery_message = res['error_message']
    
    def calculate_nso_lines(self,order):
        sale_order_line_obj = self.env['sale.order.line'].sudo()
        delivery_product = self.env.ref('delivery.product_product_delivery').sudo()
        
        
        for line in order.order_line:
            if line.location_id:
                nso_location_lines = order.order_line.filtered(lambda r: r.location_id.nso_location_id == line.location_id.nso_location_id)
                if nso_location_lines:
                    delivery_charge = 0.0
                    for n_line in nso_location_lines:
                       delivery_charge += n_line.delivery_charge
                nso_line = order.order_line.filtered(lambda r: r.name == "Total Shipping and Handling Fees(" + line.location_id.nso_location_id.country_id.name + ")")
                 
                if nso_line:
                    nso_line.write({'price_unit':delivery_charge})
                else:
                    vals = {
                            'order_id':order.id,
                            'name': "Total Shipping and Handling Fees(" + line.location_id.nso_location_id.country_id.name + ")",
                            'product_id':delivery_product.id,
                            'product_uom': delivery_product.sudo().uom_id.id,
                            'price_unit':delivery_charge,
                            'product_uom_qty':1.0,
                            'is_nso_delivery_line':True
                            }
                    if delivery_charge > 0:
                        sale_order_line_obj.create(vals)
                        
                        
    def recalculate_nso_lines(self,order):
        nso_delivery_lines = order.order_line.filtered(lambda r:r.is_nso_delivery_line)
        nso_delivery_lines.update({'delivery_charge':0.0})
        res_config = self.env['payment.handling.config'].sudo().search([],limit=1)
        handling_charge = res_config.handling_charge
        payment_processing_fee = res_config.payment_processing_fee
        transaction_value = res_config.transaction_value
        
        for line in order.order_line:
            if line.location_id:
                if line.location_id.nso_location_id.country_id == order.partner_shipping_id.country_id:
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
                            order.calculate_nso_lines(order)
                else:
                    country_code = line.location_id.nso_location_id.country_id.code
                    carrier = line.delivery_method if line.delivery_method else False  
                    country_id = line.location_id.nso_location_id.country_id
                    delivery_price = 0.0
                    lines_to_change = {}
                     
                    if carrier:
                        for so_line in order.order_line:
                            if so_line.location_id:
                                if so_line.location_id.nso_location_id.country_id.code == country_code:
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
                                    order.calculate_nso_lines(order)
                            delivery_line_track_ids = self.env['delivery.line.track'].sudo().search([
                                                                                                        ('country_id','=',country_id.id),
                                                                                                        ('order_id','=',order.id),
                                                                                                        ('is_vendor_track','=',False)
                                                                                                        ],limit=1)
                            if delivery_line_track_ids:
                                delivery_line_track_ids.update({
                                                                'carrier_id':carrier.id,
                                                                'delivery_price': round(delivery_price,2),
                                                                'is_vendor_track':False,})
                            else:
                                self.env['delivery.line.track'].sudo().create({
                                                                                  'country_id':country_id.id,
                                                                                  'order_id' : order.id,
                                                                                  'carrier_id': carrier.id,
                                                                                  'delivery_price':round(delivery_price,2),
                                                                                  'is_vendor_track':False,
                                                                                  })
                             
    
    
    def check_blank_nso_delivery_lines(self): 
        for line in self.order_line:
            if line.is_nso_delivery_line and line.delivery_charge <= 0:
                line.unlink()
                self.recalculate_nso_lines(self)
            
