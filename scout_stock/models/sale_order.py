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
    
    def send_sale_order_email(self,order,line_list):
        for location_id in line_list:
            if location_id:
                location = self.env['stock.location'].sudo().search([('id','=',int(location_id))])
#                 partner = self.env['res.partner'].sudo().search([('storefront_location_id','=',location_id)])
                partner = location.nso_location_id
                if partner:
                    template_id = self.env.ref('scout_stock.email_template_edi_sale_line', False)
                    if template_id:
                        template_id.sudo().write({
                          'email_to': str(partner.email),
                          'email_from': 'devteam.geminatec@gmail.com',
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
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
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
    
# class ProcurementGroupInherit(models.Model):
#     
#     _inherit = 'procurement.group'
#     
#     
#     @api.model
#     def _search_rule(self, route_ids, product_id, warehouse_id, domain):
#         """ First find a rule among the ones defined on the procurement
#         group, then try on the routes defined for the product, finally fallback
#         on the default behavior
#         """
#         if warehouse_id:
#             domain = expression.AND([['|', ('warehouse_id', '=', warehouse_id.id), ('warehouse_id', '=', False)], domain])
#         Rule = self.env['stock.rule']
#         res = self.env['stock.rule']
#         if 'src_loc' in self._context:
#             location_context = self._context['src_loc']
#             if location_context:
#                 domain = expression.AND([[('location_src_id','=',location_context.id)], domain])
#         if route_ids:
#             res = Rule.search(expression.AND([[('route_id', 'in', route_ids.ids)], domain]), order='route_sequence, sequence', limit=1)
#         if not res:
#             product_routes = product_id.route_ids | product_id.categ_id.total_route_ids
#             if product_routes:
#                 res = Rule.search(expression.AND([[('route_id', 'in', product_routes.ids)], domain]), order='route_sequence, sequence', limit=1)
#         if not res and warehouse_id:
#             warehouse_routes = warehouse_id.route_ids
#             if warehouse_routes:
#                 res = Rule.search(expression.AND([[('route_id', 'in', warehouse_routes.ids)], domain]), order='route_sequence, sequence', limit=1)
#         return res
    
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    def _check_order_line_carrier(self, order):
        self.ensure_one()
        carrier = False
        DeliveryCarrier = self.env['delivery.carrier']
        for line in order.order_line:
            if line.location_id:
                if order.partner_shipping_id.country_id.code == 'PH' and line.location_id.nso_location_id.country_id.code == 'PH':
                    line.delivery_method = False
                    carrier = self.env['delivery.carrier'].sudo().search([('name','=','j&T Express')],limit=1)
                    line.delivery_method = carrier.id
                    line.delivery_charge = False
#                     price_jt = line.delivery_method._get_jt_order_line_price(order,line)
                    price_jt = line.delivery_method.base_on_jt_configuration_rate_shipment(order,line)
                    print('=======11====price====================',price_jt)
                    if price_jt['success']:
                        line.delivery_charge = price_jt['price']
                        line.line_delivery_message = price_jt['warning_message']
                    else:
                        line.delivery_price = 0.0
                        line.line_delivery_message = price_jt['error_message']
                else:
                    line.delivery_method = False
                    carrier = self.env['delivery.carrier'].sudo().search([('name','=','UPS International')],limit=1)
                    line.delivery_method = carrier.id
                    line.delivery_charge = False
                    res = line.delivery_method.ups_rate_line_shipment(order,line)
                    print('====22=======price====================',res)
                    if res['success']:
                        line.delivery_charge = res['price']
                        line.line_delivery_message = res['warning_message']
                    else:
                        line.delivery_price = 0.0
                        line.line_delivery_message = res['error_message']
        print('==========delivery_message=========================',order.delivery_message)
    
    def _create_delivery_line(self, carrier, price_unit):
        SaleOrderLine = self.env['sale.order.line']
        if self.partner_id:
            # set delivery detail in the customer language
            carrier = carrier.with_context(lang=self.partner_id.lang)

        # Apply fiscal position
        taxes = carrier.product_id.taxes_id.filtered(lambda t: t.company_id.id == self.company_id.id)
        taxes_ids = taxes.ids
        if self.partner_id and self.fiscal_position_id:
            taxes_ids = self.fiscal_position_id.map_tax(taxes, carrier.product_id, self.partner_id).ids

        # Create the sales order line
        carrier_with_partner_lang = carrier.with_context(lang=self.partner_id.lang)
        if carrier_with_partner_lang.product_id.description_sale:
            so_description = '%s: %s' % (carrier_with_partner_lang.name,
                                        carrier_with_partner_lang.product_id.description_sale)
        else:
            so_description = carrier_with_partner_lang.name
        line_subtotal = sum(line.delivery_charge for line in self.order_line)
        values = {
            'order_id': self.id,
            'name': so_description,
            'product_uom_qty': 1,
            'product_uom': carrier.product_id.uom_id.id,
            'product_id': carrier.product_id.id,
            'price_unit': line_subtotal,
            'tax_id': [(6, 0, taxes_ids)],
            'is_delivery': True,
        }
        if self.order_line:
            values['sequence'] = self.order_line[-1].sequence + 1
        sol = SaleOrderLine.sudo().create(values)
        return sol

    
# class DeliveryCarrier(models.Model):
#     _inherit = 'delivery.carrier'
#     
#     def ups_rate_line_shipment(self, order,line):
#         superself = self.sudo()
#         srm = UPSRequest(self.log_xml, superself.ups_username, superself.ups_passwd, superself.ups_shipper_number, superself.ups_access_number, self.prod_environment)
#         ResCurrency = self.env['res.currency']
#         max_weight = self.ups_default_packaging_id.max_weight
#         packages = []
#         total_qty = 0
#         total_weight = 0
#         for line in line.filtered(lambda line: not line.is_delivery):
#             total_qty += line.product_uom_qty
#             total_weight += line.product_id.weight * line.product_qty
# 
#         if max_weight and total_weight > max_weight:
#             total_package = int(total_weight / max_weight)
#             last_package_weight = total_weight % max_weight
# 
#             for seq in range(total_package):
#                 packages.append(Package(self, max_weight))
#             if last_package_weight:
#                 packages.append(Package(self, last_package_weight))
#         else:
#             packages.append(Package(self, total_weight))
# 
#         shipment_info = {
#             'total_qty': total_qty  # required when service type = 'UPS Worldwide Express Freight'
#         }
# 
#         if self.ups_cod:
#             cod_info = {
#                 'currency': order.partner_id.country_id.currency_id.name,
#                 'monetary_value': line.delivery_charge,
#                 'funds_code': self.ups_cod_funds_code,
#             }
#         else:
#             cod_info = None
# 
#         check_value = srm.check_required_value(order.company_id.partner_id, order.warehouse_id.partner_id, order.partner_shipping_id, order=order)
#         if check_value:
#             return {'success': False,
#                     'price': 0.0,
#                     'error_message': check_value,
#                     'warning_message': False}
# 
#         ups_service_type = order.ups_service_type or self.ups_default_service_type
#         result = srm.get_shipping_price(
#             shipment_info=shipment_info, packages=packages, shipper=order.company_id.partner_id, ship_from=order.warehouse_id.partner_id,
#             ship_to=order.partner_shipping_id, packaging_type=self.ups_default_packaging_id.shipper_package_code, service_type=ups_service_type,
#             saturday_delivery=self.ups_saturday_delivery, cod_info=cod_info)
# 
#         if result.get('error_message'):
#             return {'success': False,
#                     'price': 0.0,
#                     'error_message': _('Error:\n%s') % result['error_message'],
#                     'warning_message': False}
# 
#         if order.currency_id.name == result['currency_code']:
#             price = float(result['price'])
#         else:
#             quote_currency = ResCurrency.search([('name', '=', result['currency_code'])], limit=1)
#             price = quote_currency._convert(
#                 float(result['price']), order.currency_id, order.company_id, order.date_order or fields.Date.today())
# 
#         if self.ups_bill_my_account and order.ups_carrier_account:
#             # Don't show delivery amount, if ups bill my account option is true
#             price = 0.0
# 
#         return {'success': True,
#                 'price': price,
#                 'error_message': False,
#                 'warning_message': False}
#         
#     def _get_jt_order_line_price(self,order,line):
#         self.ensure_one()
#         destination_id = order.partner_shipping_id.state_id
#         origin_id = False
#         total_weight = 0.0
#         total_weight_remain = 0.0
#         big_product_count =0.0
#         total_delivery_cost = 0.0
#         total_rate =0.0
#         big_product_price = order.carrier_id.big_size_price
#         for line in line:
#             if line.location_id.state_id:
#                 origin_id = line.location_id.state_id
#             total_weight += (line.product_id.weight * line.product_uom_qty)
#             
#             if line.product_id.is_big_size:
#                 big_product_count += (line.product_uom_qty * 1)
#         print('============origin_id===destination_id=========================',origin_id,destination_id)
#         if origin_id and destination_id:
#             total_weight_remain = total_weight
#             shipping_rates = self.env['jt.shipping.rates'].sudo().search([
#                                                                           ('origin_id','=',origin_id.id),
#                                                                           ('state_id','=',destination_id.id),
#                                                                           ('min_weight','<',total_weight),
#                                                                           ('max_weight','>=',total_weight),
#                                                                           ],limit=1)
#             if shipping_rates:
#                 total_delivery_cost += shipping_rates.rate
#                 
#             elif total_weight_remain > 0:
#                 while total_weight_remain > 0:
#                     data = self.get_maximum_shipping_rate(origin_id,destination_id,total_weight_remain)
#                     total_weight_remain = data['remain']
#                     total_delivery_cost += data['rate']
#                     
#             if big_product_count > 0:
#                 total_delivery_cost += (big_product_count * big_product_price)
#             
#         return total_delivery_cost
        
