from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import pdf
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.delivery_ups.models.ups_request import UPSRequest, Package

class UPSDeliveryCarrier(models.Model):
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
    
#     def order_line_jt_configuration_rate_shipment(self, order, line):
#         carrier = self._match_address(order.partner_shipping_id)
#         if not carrier:
#             return {'success': False,
#                     'price': 0.0,
#                     'error_message': _('Error: no matching grid.'),
#                     'warning_message': False}
# 
#         try:
#             price_unit = self._get_jt_price_available(order,line)
#         except UserError as e:
#             return {'success': False,
#                     'price': 0.0,
#                     'error_message': e.name,
#                     'warning_message': False}
#         if order.company_id.currency_id.id != order.pricelist_id.currency_id.id:
#             price_unit = order.company_id.currency_id.with_context(date=order.date_order).compute(price_unit, order.pricelist_id.currency_id)
# 
#         return {'success': True,
#                 'price': price_unit,
#                 'error_message': False,
#                 'warning_message': False}
#     
#     def get_maximum_shipping_rate(self,origin_id,destination_id,total_weight_remaining):
#         print('======================max_shipping_rate==================1====',origin_id,destination_id,total_weight_remaining)
#         shipping_rates = self.env['jt.shipping.rates'].sudo().search([
#                                                                         ('origin_id','=',origin_id.id),
#                                                                         ('state_id','=',destination_id.id),
#                                                                         ])
#         
# #         if not shipping_rates:
# #             shipping_rates = self.env['jt.shipping.rates'].sudo().search([
# #                                                                         ('origin_id','=',origin_id.id),
# #                                                                         ('state_id','=',destination_id.id),
# #                                                                         ('min_weight','<',total_weight_remaining),
# #                                                                         ('max_weight','>=',total_weight_remaining),
# #                                                                         ])
#         
#         shipping_rate_list = []
#         shipping_rate_list2 = []
#         shipping_need_max = True
#         max_rate = 0.0
#         max_shipping_rate = False
#         for rates in shipping_rates:
#             if rates.max_weight <= total_weight_remaining:
#                 shipping_rate_list.append(rates.max_weight)
#             elif rates.max_weight >= total_weight_remaining:
#                 shipping_need_max = False
#             
#         if len(shipping_rate_list) > 0 and shipping_need_max:
#             max_rate = max(shipping_rate_list)
#             max_rate_record = self.env['jt.shipping.rates'].sudo().search([
#                                                                         ('origin_id','=',origin_id.id),
#                                                                         ('state_id','=',destination_id.id),
#                                                                         ('max_weight','=',max_rate)
#                                                                        ])
#             if max_rate_record:
#                 max_rate = max_rate_record.rate
#         
#         else:
#             shipping_rates_2 = self.env['jt.shipping.rates'].sudo().search([
#                                                                           ('origin_id','=',origin_id.id),
#                                                                           ('state_id','=',destination_id.id),
#                                                                           ('min_weight','<=',total_weight_remaining),
#                                                                           ('max_weight','>=',total_weight_remaining)
#                                                                           ])
#             if shipping_rates_2:
#                 for rate2 in shipping_rates_2:
#                     shipping_rate_list2.append(rate2.max_weight)
#                 
#                 if len(shipping_rates_2) > 0:
#                     max_rate = max(shipping_rate_list2)
#                     
#                     max_rate_record = self.env['jt.shipping.rates'].sudo().search([
#                                                                         ('origin_id','=',origin_id.id),
#                                                                         ('state_id','=',destination_id.id),
#                                                                         ('max_weight','=',max_rate)
#                                                                        ])
#                     if max_rate_record:
#                         max_rate = max_rate_record.rate
#                     
#                     
#         if max_rate > 0:
#             max_shipping_rate = self.env['jt.shipping.rates'].sudo().search([
#                                                                         ('origin_id','=',origin_id.id),
#                                                                         ('state_id','=',destination_id.id),
#                                                                         ('rate','=',max_rate)
#                                                                        ])
#             print('======================max_shipping_rate======================',max_shipping_rate)
#             if max_shipping_rate:
#                     total_weight_remain = total_weight_remaining - max_shipping_rate.max_weight
#                     rate = max_shipping_rate.rate
#                     return {'rate':rate,'remain':total_weight_remain}
#     
#     def _get_jt_price_available(self,order,line):
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
#         print('============origin_id===destination_id==========33===============',origin_id,destination_id)
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
    
