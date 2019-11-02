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
    
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    def _check_order_line_carrier(self, order):
        self.ensure_one()
        carrier = False
        DeliveryCarrier = self.env['delivery.carrier']
        for line in order.order_line:
            if line.location_id:
                if not line.product_id.type == 'service':
                    if order.partner_shipping_id.country_id.code == 'PH' and line.location_id.nso_location_id.country_id.code == 'PH':
                        line.delivery_method = False
                        carrier = self.env['delivery.carrier'].sudo().search([('name','=','j&T Express')],limit=1)
                        line.delivery_method = carrier.id
                        line.delivery_charge = False
    #                     price_jt = line.delivery_method._get_jt_order_line_price(order,line)
                        price_jt = line.delivery_method.base_on_jt_configuration_rate_shipment(order,line)
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
                        if res['success']:
                            line.delivery_charge = res['price']
                            line.line_delivery_message = res['warning_message']
                        else:
                            line.delivery_price = 0.0
                            line.line_delivery_message = res['error_message']
    
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
        
