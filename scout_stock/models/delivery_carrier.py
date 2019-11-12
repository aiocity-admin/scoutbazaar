from odoo import api, models, fields, _
from odoo import _
from odoo.exceptions import UserError
from odoo.tools import pdf
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.delivery_ups.models.ups_request import UPSRequest, Package
from odoo.addons.delivery_easypost.models.easypost_request import EasypostRequest
import json
import requests
from werkzeug.urls import url_join
from odoo.tools.float_utils import float_round, float_is_zero

class UPSDeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'
    
    
    shipping_range = fields.Selection([('local','Local'),('international','International')],string="Shipping Range")
    source_country_ids = fields.Many2many('res.country', string='Source Countries')
    
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
    
    
    def fixed_rate_line_shipment(self, order,line):
        carrier = self._match_address(order.partner_shipping_id)
        if not carrier:
            return {'success': False,
                    'price': 0.0,
                    'error_message': _('Error: this delivery method is not available for this address.'),
                    'warning_message': False}
        price = self.fixed_price
        if self.company_id and self.company_id.currency_id.id != order.currency_id.id:
            price = self.company_id.currency_id._convert(price,order.currency_id,order.company_id,fields.Date.today())
        return {'success': True,
                'price': price,
                'error_message': False,
                'warning_message': False,
                'currency_code':order.currency_id.name}
    
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
        stage_ids = self.env['stock.location.route'].sudo().search([('name','=','Dropship')])
        if not line.location_id and line.product_id.route_ids in stage_ids:
            vendor = self.get_stock_vendor(order,line)
            if vendor:
                check_value = srm.check_required_value(vendor, vendor,order.partner_shipping_id, order=order)
        else:
            check_value = srm.check_required_value(line.location_id.nso_location_id,line.location_id.nso_location_id, order.partner_shipping_id, order=order)
#         check_value = srm.check_required_value(line.location_id.nso_location_id,line.location_id.nso_location_id, order.partner_shipping_id, order=order)
        
        if check_value:
            return {'success': False,
                    'price': 0.0,
                    'error_message': check_value,
                    'warning_message': False}

        ups_service_type = order.ups_service_type or self.ups_default_service_type
        
        if not line.location_id and line.product_id.route_ids in stage_ids:
            vendor = self.get_stock_vendor(order,line)
            if vendor:
                result = srm.get_shipping_price(
                    shipment_info=shipment_info, packages=packages, shipper=vendor, ship_from=vendor,
                    ship_to=order.partner_shipping_id, packaging_type=self.ups_default_packaging_id.shipper_package_code, service_type=ups_service_type,
                    saturday_delivery=self.ups_saturday_delivery, cod_info=cod_info)
            
        else:
            result = srm.get_shipping_price(
                shipment_info=shipment_info, packages=packages, shipper=line.location_id.nso_location_id, ship_from=line.location_id.nso_location_id,
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
                float(result['price']), order.currency_id, order.company_id,fields.Date.today())
        if self.ups_bill_my_account and order.ups_carrier_account:
            # Don't show delivery amount, if ups bill my account option is true
            price = 0.0

        return {'success': True,
                'price': price,
                'error_message': False,
                'warning_message': False,
                'currency_code':result.get('currency_code')}
    
    def ups_send_shipping(self, pickings):
        res = []
        superself = self.sudo()
        srm = UPSRequest(self.log_xml, superself.ups_username, superself.ups_passwd, superself.ups_shipper_number, superself.ups_access_number, self.prod_environment)
        ResCurrency = self.env['res.currency']
        for picking in pickings:
            packages = []
            package_names = []
            if picking.package_ids:
                # Create all packages
                for package in picking.package_ids:
                    packages.append(Package(self, package.shipping_weight, quant_pack=package.packaging_id, name=package.name))
                    package_names.append(package.name)
            # Create one package with the rest (the content that is not in a package)
            if picking.weight_bulk:
                packages.append(Package(self, picking.weight_bulk))

            invoice_line_total = 0
            for move in picking.move_lines:
                invoice_line_total += picking.company_id.currency_id.round(move.product_id.lst_price * move.product_qty)

            shipment_info = {
                'description': picking.origin,
                'total_qty': sum(sml.qty_done for sml in picking.move_line_ids),
                'ilt_monetary_value': '%d' % invoice_line_total,
                'itl_currency_code': self.env.user.company_id.currency_id.name,
                'phone': picking.partner_id.mobile or picking.partner_id.phone or picking.sale_id.partner_id.mobile or picking.sale_id.partner_id.phone,
            }
            if picking.sale_id and picking.sale_id.carrier_id != picking.carrier_id:
                ups_service_type = picking.carrier_id.ups_default_service_type or picking.ups_service_type or self.ups_default_service_type
            else:
                ups_service_type = picking.ups_service_type or self.ups_default_service_type
            ups_carrier_account = picking.ups_carrier_account

            if picking.carrier_id.ups_cod:
                cod_info = {
                    'currency': picking.partner_id.country_id.currency_id.name,
                    'monetary_value': picking.sale_id.amount_total,
                    'funds_code': self.ups_cod_funds_code,
                }
            else:
                cod_info = None

            check_value = srm.check_required_value(picking.location_id.nso_location_id, picking.location_id.nso_location_id, picking.partner_id, picking=picking)
            if check_value:
                raise UserError(check_value)

            package_type = picking.package_ids and picking.package_ids[0].packaging_id.shipper_package_code or self.ups_default_packaging_id.shipper_package_code
            result = srm.send_shipping(
                shipment_info=shipment_info, packages=packages, shipper=picking.location_id.nso_location_id, ship_from=picking.location_id.nso_location_id,
                ship_to=picking.partner_id, packaging_type=package_type, service_type=ups_service_type, label_file_type=self.ups_label_file_type, ups_carrier_account=ups_carrier_account,
                saturday_delivery=picking.carrier_id.ups_saturday_delivery, cod_info=cod_info)
            if result.get('error_message'):
                raise UserError(result['error_message'])

            order = picking.sale_id
            company = order.company_id or picking.company_id or self.env.user.company_id
            currency_order = picking.sale_id.currency_id
            if not currency_order:
                currency_order = picking.company_id.currency_id

            if currency_order.name == result['currency_code']:
                price = float(result['price'])
            else:
                quote_currency = ResCurrency.search([('name', '=', result['currency_code'])], limit=1)
                price = quote_currency._convert(
                    float(result['price']), currency_order, company, order.date_order or fields.Date.today())

            package_labels = []
            for track_number, label_binary_data in result.get('label_binary_data').items():
                package_labels = package_labels + [(track_number, label_binary_data)]

            carrier_tracking_ref = "+".join([pl[0] for pl in package_labels])
            logmessage = _("Shipment created into UPS<br/>"
                           "<b>Tracking Numbers:</b> %s<br/>"
                           "<b>Packages:</b> %s") % (carrier_tracking_ref, ','.join(package_names))
            if self.ups_label_file_type != 'GIF':
                attachments = [('LabelUPS-%s.%s' % (pl[0], self.ups_label_file_type), pl[1]) for pl in package_labels]
            if self.ups_label_file_type == 'GIF':
                attachments = [('LabelUPS.pdf', pdf.merge_pdf([pl[1] for pl in package_labels]))]
            picking.message_post(body=logmessage, attachments=attachments)
            shipping_data = {
                'exact_price': price,
                'tracking_number': carrier_tracking_ref}
            res = res + [shipping_data]
        return res 
    
    def easypost_rate_line_shipment(self, order,line):
        """ Return the rates for a quotation/SO."""
        ep = EasypostRequest(self.easypost_production_api_key if self.prod_environment else self.easypost_test_api_key, self.log_xml)
#         response = ep.rate_request(self, order.partner_shipping_id, line.location_id.nso_location_id, order,picking=False,line=line)
        # Return error message
        response = False
        stage_ids = self.env['stock.location.route'].sudo().search([('name','=','Dropship')])
        if not line.location_id and line.product_id.route_ids in stage_ids:
            vendor = self.get_stock_vendor(order,line)
            if vendor:
                response = ep.rate_request(self, order.partner_shipping_id, vendor, order,picking=False,line=line)
        else:
            response = ep.rate_request(self, order.partner_shipping_id, line.location_id.nso_location_id, order,picking=False,line=line)
        
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
            'warning_message': response.get('warning_message', False),
            'currency_code':rate.get('currency')
        }
    
    def easypost_send_shipping(self, pickings):
        """ It creates an easypost order and buy it with the selected rate on
        delivery method or cheapest rate if it is not set. It will use the
        packages used with the put in pack functionality or a single package if
        the user didn't use packages.
        Once the order is purchased. It will post as message the tracking
        links and the shipping labels.
        """
        res = []
        ep = EasypostRequest(self.easypost_production_api_key if self.prod_environment else self.easypost_test_api_key, self.log_xml)
        for picking in pickings:
            result = ep.send_shipping(self, picking.partner_id, picking.location_id.nso_location_id, picking=picking)
            if result.get('error_message'):
                raise UserError(_(result['error_message']))
            rate = result.get('rate')
            if rate['currency'] == picking.company_id.currency_id.name:
                price = rate['rate']
            else:
                quote_currency = self.env['res.currency'].search([('name', '=', rate['currency'])], limit=1)
                price = quote_currency._convert(float(rate['rate']), picking.company_id.currency_id, self.env['res.users']._get_company(), fields.Date.today())
                
            # return tracking information
            carrier_tracking_link = ""
            for track_number, tracker_url in result.get('track_shipments_url').items():
                carrier_tracking_link += '<a href=' + tracker_url + '>' + track_number + '</a><br/>'
                
            carrier_tracking_ref = ' + '.join(result.get('track_shipments_url').keys())
            
            labels = []
            for track_number, label_url in result.get('track_label_data').items():
                label = requests.get(label_url)
                labels.append(('LabelEasypost-%s.%s' % (track_number, self.easypost_label_file_type), label.content))
            
            logmessage = (_("Shipping label for packages"))
            picking.message_post(body=logmessage, attachments=labels)
            picking.message_post(body=carrier_tracking_link)
            
            shipping_data = {'exact_price': price,
                             'tracking_number': carrier_tracking_ref}
            res = res + [shipping_data]
            # store order reference on picking
            picking.ep_order_ref = result.get('id')
        return res
    
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
            a = carrier._generate_services(rates)
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
    
    