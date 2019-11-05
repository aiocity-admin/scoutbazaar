from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import pdf
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.delivery_ups.models.ups_request import UPSRequest, Package
from odoo.addons.delivery_easypost.models.easypost_request import EasypostRequest

class UPSDeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'
    
    
    shipping_range = fields.Selection([('local','Local'),('international','International')],string="Shipping Range")
    
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
        
        check_value = srm.check_required_value(order.company_id.partner_id,line.location_id.nso_location_id, order.partner_shipping_id, order=order)
        
        if check_value:
            return {'success': False,
                    'price': 0.0,
                    'error_message': check_value,
                    'warning_message': False}

        ups_service_type = order.ups_service_type or self.ups_default_service_type
        result = srm.get_shipping_price(
            shipment_info=shipment_info, packages=packages, shipper=order.company_id.partner_id, ship_from=line.location_id.nso_location_id,
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
        
        
    def easypost_rate_line_shipment(self, order,line):
        """ Return the rates for a quotation/SO."""
        ep = EasypostRequest(self.easypost_production_api_key if self.prod_environment else self.easypost_test_api_key, self.log_xml)
        response = ep.rate_request(self, order.partner_shipping_id, line.location_id.nso_location_id, order,picking=False,line=line)
        # Return error message
        if response.get('error_message'):
            return {
                'success': False,
                'price': 0.0,
                'error_message': response.get('error_message'),
                'warning_message': False
            }

        # Update price with the order currency
        rate = response.get('rate')
        if order.currency_id.name == rate['currency']:
            price = float(rate['rate'])
        else:
            quote_currency = self.env['res.currency'].search([('name', '=', rate['currency'])], limit=1)
            price = quote_currency._convert(float(rate['rate']), order.currency_id, self.env['res.users']._get_company(), fields.Date.today())

        return {
            'success': True,
            'price': price,
            'error_message': False,
            'warning_message': response.get('warning_message', False)
        }
        
        
class EasypostRequest(EasypostRequest):
    
    
    def _prepare_order_shipments(self, carrier, order,line):
        """ Method used in order to estimate delivery
        cost for a quotation. It estimates the price with
        the default package defined on the carrier.
        e.g: if the default package on carrier is a 10kg Fedex
        box and the customer ships 35kg it will create a shipment
        with 4 packages (3 with 10kg and the last with 5 kg.).
        It ignores reality with dimension or the fact that items
        can not be cut in multiple pieces in order to allocate them
        in different packages. It also ignores customs info.
        """
        # Max weight for carrier default package
        max_weight = carrier._easypost_convert_weight(carrier.easypost_default_packaging_id.max_weight)
        # Order weight
        total_weight = carrier._easypost_convert_weight(line.product_id.weight * line.product_uom_qty)
        # Create shipments
        shipments = {}
        if max_weight and total_weight > max_weight:
            # Integer division for packages with maximal weight.
            total_shipment = int(total_weight // max_weight)
            # Remainder for last package.
            last_shipment_weight = float_round(total_weight % max_weight, precision_digits=1)
            for shp_id in range(0, total_shipment):
                shipments.update(self._prepare_parcel(shp_id, carrier.easypost_default_packaging_id, max_weight, carrier.easypost_label_file_type))
            if not float_is_zero(last_shipment_weight, precision_digits=1):
                shipments.update(self._prepare_parcel(total_shipment, carrier.easypost_default_packaging_id, last_shipment_weight, carrier.easypost_label_file_type))
        else:
            shipments.update(self._prepare_parcel(0, carrier.easypost_default_packaging_id, total_weight, carrier.easypost_label_file_type))
        return shipments
    
    
    
    def rate_request(self, carrier, recipient, shipper, order=False, picking=False,line=False):
        
        self._check_required_value(carrier, recipient, shipper, order=order, picking=picking)

        order_payload = {}

        # Add current carrier type
        order_payload['order[carrier_accounts][id]'] = carrier.easypost_delivery_type_id

        order_payload.update(self._prepare_address('to_address', recipient))
        order_payload.update(self._prepare_address('from_address', shipper))

        if picking:
            order_payload.update(self._prepare_picking_shipments(carrier, picking))
        else:
            order_payload.update(self._prepare_order_shipments(carrier, order,line))

        response = self._make_api_request("orders", "post", data=order_payload)
        error_message = False
        warning_message = False
        rate = False
        if response.get('messages'):
            warning_message = ('\n'.join([x['carrier'] + ': ' + x['type'] + ' -- ' + x['message'] for x in response['messages']]))
            response.update({'warning_message': warning_message})

        rates = response.get('rates')
        if not rates:
            error_message = _("It seems Easypost do not provide shipments for this order.\
                We advise you to try with another package type or service level.")
        elif rates and not carrier.easypost_default_service_id:
            rate = self._sort_rates(rates)[0]
            carrier._generate_services(rates)
        elif rates and carrier.easypost_default_service_id:
            rate = [rate for rate in rates if rate['service'] == carrier.easypost_default_service_id.name]
            if not rate:
                error_message = _("There is no rate available for the selected service level for one of your package. Please choose another service level.")
            else:
                rate = rate[0]

        if error_message and warning_message:
            error_message += warning_message

        response.update({
            'error_message': error_message,
            'rate': rate,
        })

        return response
