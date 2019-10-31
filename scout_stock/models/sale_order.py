from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import pdf
from odoo.addons.delivery_ups.models.ups_request import UPSRequest, Package

class SaleOrderLine(models.Model):
    
    _inherit='sale.order.line'
    
    location_id = fields.Many2one("stock.location", string="Location")
    delivery_charge = fields.Float(string="Delivery Charge")
    delivery_method = fields.Many2one("delivery.carrier", string="Delivery Method")
    
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
                        print('==============================a=====',a)
    
    
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    total_delivery_amount = fields.Monetary(string='Delivery Amount',
        store=True, readonly=True, compute='_compute_delivery_amount', track_visibility='always')
    
    def _get_delivery_methods(self):
        address = self.partner_shipping_id
        # searching on website_published will also search for available website (_search method on computed field)
        return self.env['delivery.carrier'].sudo().search([('website_published', '=', True)]).available_carriers(address)

    
    @api.one
    @api.depends('total_delivery_amount')
    def _compute_delivery_amount(self):
        self.total_delivery_amount = sum(line.delivery_charge for line in self.order_line)
        
    @api.depends('order_line.price_unit', 'order_line.tax_id', 'order_line.discount', 'order_line.product_uom_qty')
    def _compute_amount_delivery(self):
        for order in self:
            order.amount_delivery = sum(line.delivery_charge for line in self.order_line)
    
    def _check_order_line_carrier(self, order):
        self.ensure_one()
        carrier = False
        DeliveryCarrier = self.env['delivery.carrier']
        for line in order.order_line:
            if line.location_id:
                if order.partner_shipping_id.country_id.code == 'PH' and line.location_id.nso_lication_id.country_id.code == 'PH':
                    carrier = self.env['delivery.carrier'].sudo().search([('name','=','j&T Express')],limit=1)
                    line.delivery_method = carrier.id
                else:
                    carrier = self.env['delivery.carrier'].sudo().search([('name','=','UPS International')],limit=1)
                    line.delivery_method = carrier.id
                    price = line.delivery_method.ups_rate_line_shipment(order,line)
                    print('===========price====================',price)
                    if price['price']:
                        line.delivery_charge = price['price']
                    else:
                        line.delivery_charge = 0.0
        
#         order.amount_delivery = total_delivery
#         return bool(carrier)
#     def get_order_line_delivery_price(self,line,order):
#         res = line.delivery_method.order_line_rate(line)
#         print('===============res===============',res)
#         line.delivery_charge = res['price']
#     @api.model
#     def check_ups_service_type(self, value):
#         if value.get('sale_id'):
#             order = self.browse(int(value['sale_id']))
#             order.ups_service_type = value.get('ups_service_type')
#             check = order.carrier_id.ups_rate_shipment(order)
#             if check['success']:
#                 return {}
#             else:
#                 order.ups_service_type = order.carrier_id.ups_default_service_type
#                 return {'error': check['error_message']}

    
class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'
    
    def ups_rate_line_shipment(self, order,line):
        superself = self.sudo()
        srm = UPSRequest(self.log_xml, superself.ups_username, superself.ups_passwd, superself.ups_shipper_number, superself.ups_access_number, self.prod_environment)
        ResCurrency = self.env['res.currency']
        max_weight = self.ups_default_packaging_id.max_weight
        packages = []
        total_qty = 0
        total_weight = 0
        for line in line.filtered(lambda line: not line.is_delivery):
            print('================ups_rate_shipment============================',line)
            total_qty += line.product_uom_qty
            total_weight += line.product_id.weight * line.product_qty

        if max_weight and total_weight > max_weight:
            total_package = int(total_weight / max_weight)
            last_package_weight = total_weight % max_weight

            for seq in range(total_package):
                packages.append(Package(self, max_weight))
            if last_package_weight:
                packages.append(Package(self, last_package_weight))
        else:
            packages.append(Package(self, total_weight))

        shipment_info = {
            'total_qty': total_qty  # required when service type = 'UPS Worldwide Express Freight'
        }

        if self.ups_cod:
            cod_info = {
                'currency': order.partner_id.country_id.currency_id.name,
                'monetary_value': line.delivery_charge,
                'funds_code': self.ups_cod_funds_code,
            }
        else:
            cod_info = None

        check_value = srm.check_required_value(order.company_id.partner_id, order.warehouse_id.partner_id, order.partner_shipping_id, order=order)
        if check_value:
            return {'success': False,
                    'price': 0.0,
                    'error_message': check_value,
                    'warning_message': False}

        ups_service_type = order.ups_service_type or self.ups_default_service_type
        result = srm.get_shipping_price(
            shipment_info=shipment_info, packages=packages, shipper=order.company_id.partner_id, ship_from=order.warehouse_id.partner_id,
            ship_to=order.partner_shipping_id, packaging_type=self.ups_default_packaging_id.shipper_package_code, service_type=ups_service_type,
            saturday_delivery=self.ups_saturday_delivery, cod_info=cod_info)

        if result.get('error_message'):
            return {'success': False,
                    'price': 0.0,
                    'error_message': _('Error:\n%s') % result['error_message'],
                    'warning_message': False}

        if order.currency_id.name == result['currency_code']:
            price = float(result['price'])
        else:
            quote_currency = ResCurrency.search([('name', '=', result['currency_code'])], limit=1)
            price = quote_currency._convert(
                float(result['price']), order.currency_id, order.company_id, order.date_order or fields.Date.today())

        if self.ups_bill_my_account and order.ups_carrier_account:
            # Don't show delivery amount, if ups bill my account option is true
            price = 0.0

        return {'success': True,
                'price': price,
                'error_message': False,
                'warning_message': False}
        
        
#         if self.only_services:
#             self.write({'carrier_id': None})
#             self._remove_delivery_line()
#             return True
#         else:
#             # attempt to use partner's preferred carrier
#             if not force_carrier_id and self.partner_shipping_id.property_delivery_carrier_id:
#                 force_carrier_id = self.partner_shipping_id.property_delivery_carrier_id.id
# 
#             carrier = force_carrier_id and DeliveryCarrier.browse(force_carrier_id) or self.carrier_id
#             available_carriers = self._get_delivery_methods()
#             if carrier:
#                 if carrier not in available_carriers:
#                     carrier = DeliveryCarrier
#                 else:
#                     # set the forced carrier at the beginning of the list to be verfied first below
#                     available_carriers -= carrier
#                     available_carriers = carrier + available_carriers
#             if force_carrier_id or not carrier or carrier not in available_carriers:
#                 for delivery in available_carriers:
#                     verified_carrier = delivery._match_address(self.partner_shipping_id)
#                     if verified_carrier:
#                         carrier = delivery
#                         break
#                 self.write({'carrier_id': carrier.id})
#             self._remove_delivery_line()
#             if carrier:
#                 self.get_delivery_price()
#                 if self.delivery_rating_success:
#                     self.set_delivery_line()

        