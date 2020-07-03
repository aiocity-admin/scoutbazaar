# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import pdf
import base64
import json
import requests
import math
import logging

_logger = logging.getLogger(__name__)

class ProductPackaging(models.Model):
    _inherit = 'product.packaging'

    package_carrier_type = fields.Selection(selection_add=[('auspost', 'Aus Post')])

class ProviderAUS(models.Model):
    
    _inherit = 'delivery.carrier'
    
    
    delivery_type = fields.Selection(selection_add=[('auspost', "Aus Post")])
    
    
    pac_api_key = fields.Char(string='PAC API Key', groups="base.group_system")
    
    aus_default_packaging_id = fields.Many2one('product.packaging', string='AUS Default Packaging Type', domain="[('package_carrier_type', '=', 'auspost')]")
    
    aus_service_type = fields.Selection([('Economy Air','Economy Air'),('Regular','Regular')])
    
    letter_min_weight = fields.Integer('Letter Minimum Weight (in grams)')
    letter_max_weight = fields.Integer('Letter Maximum Weight (in grams)')
    parcel_min_weight = fields.Integer('Parcel Minimum Weight (in grams)')
    parcel_max_weight = fields.Integer('Parcel Maximum Weight (in grams)')
    
    
    
    
    def auspost_rate_line_shipment(self, order,lines):
        superself = self.sudo()
        ResCurrency = self.env['res.currency']
        total_weight = 0.1
        result = False
        no_of_parcels = 1
        api_url = False
        params = {}
        api_key_encoded = self.pac_api_key.encode('utf-8')
        headers = {"auth-key": "Basic %s" % base64.b64encode(api_key_encoded).decode('utf-8'),"Content-Type": "application/json"}
        service_code = False
        for so_line in lines:
            total_weight += ((so_line.product_uom_qty) * (so_line.product_id.weight))
        
        total_weight *= 1000
        
        if self.aus_service_type == 'Economy Air':
            service_code = False
            service_available = False
            
            if total_weight >= self.parcel_min_weight and total_weight <= self.parcel_max_weight:
                
                #Check if service code is availabe for destination country
                parcel_availabe_url = "https://digitalapi.auspost.com.au/postage/parcel/international/service"
                avail_result = requests.get(url=parcel_availabe_url,params={'country_code' : order.partner_shipping_id.country_id.code, 'weight' : total_weight},headers=headers)
                if 'services' in json.loads(avail_result.text):
                    services_dict = json.loads(avail_result.text).get('services').get('service')
                    
                    if services_dict:
                        for service in services_dict:
                            if service.get('name') == self.aus_service_type:
                                service_available = True
                                service_code = service.get('code')
                api_url = "https://digitalapi.auspost.com.au/postage/parcel/international/calculate.json"
                
            elif total_weight >= self.letter_min_weight and total_weight <= self.letter_max_weight:
                total_weight = total_weight/1000
                #Check if service code is availabe for destination country
                parcel_availabe_url = "https://digitalapi.auspost.com.au/postage/letter/international/service"
                avail_result = requests.get(url=parcel_availabe_url,params={'country_code' : order.partner_shipping_id.country_id.code, 'weight' : total_weight},headers=headers)
                if 'services' in json.loads(avail_result.text):
                    services_dict = json.loads(avail_result.text).get('services').get('service')
                    
                    if services_dict:
                        for service in services_dict:
                            if service.get('name') == self.aus_service_type:
                                service_available = True
                                service_code = service.get('code')
                api_url = "https://digitalapi.auspost.com.au/postage/letter/international/calculate.json"
                
            elif total_weight > self.parcel_max_weight:
                no_of_parcels = math.ceil(total_weight /self.parcel_max_weight)
                total_weight = self.parcel_max_weight
                total_weight = total_weight/1000
                
                
                parcel_availabe_url = "https://digitalapi.auspost.com.au/postage/parcel/international/service"
                avail_result = requests.get(url=parcel_availabe_url,params={'country_code' : order.partner_shipping_id.country_id.code, 'weight' : total_weight},headers=headers)
                if 'services' in json.loads(avail_result.text):
                    services_dict = json.loads(avail_result.text).get('services').get('service')
                    
                    if services_dict:
                        for service in services_dict:
                            if service.get('name') == self.aus_service_type:
                                service_available = True
                                service_code = service.get('code')
                
                api_url = "https://digitalapi.auspost.com.au/postage/parcel/international/calculate.json"
                
                
            _logger.info("Service Code ===  %s .", service_code, exc_info=True)    
            params.update({
                           'country_code':order.partner_shipping_id.country_id.code,
                           'weight':total_weight,
                           'service_code': service_code
                           })
        
            if api_url and params and headers and service_code and service_available:
                result = requests.get(url=api_url,params=params,headers=headers)
                result = json.loads(result.text)
            else:
                return {'success': False,
                    'price': 0.0,
                    'error_message': 'Delivery not available for this country!',
                    'warning_message': False}
        
        elif self.aus_service_type == 'Regular':
            service_code = False
            service_available = False
            if total_weight >= self.letter_min_weight and total_weight <= self.letter_max_weight:
                
                #Check if service code is availabe for destination country
                parcel_availabe_url = "https://digitalapi.auspost.com.au/postage/letter/domestic/service"
                avail_result = requests.get(url=parcel_availabe_url,params={'country_code' : order.partner_shipping_id.country_id.code, 'weight' : total_weight},headers=headers)
                if 'services' in json.loads(avail_result.text):
                    services_dict = json.loads(avail_result.text).get('services').get('service')
                    
                    if services_dict:
                        for service in services_dict:
                            if service.get('name') in ['Large Letter', 'Small Letter']:
                                service_available = True
                                service_code = service.get('code')
                                
                                
                api_url = "https://digitalapi.auspost.com.au/postage/letter/domestic/calculate.json"
            
            elif total_weight > self.letter_max_weight:
                
                no_of_parcels = int(total_weight / self.letter_max_weight)
                total_weight = self.letter_max_weight
                
                #Check if service code is availabe for destination country
                parcel_availabe_url = "https://digitalapi.auspost.com.au/postage/letter/domestic/service"
                avail_result = requests.get(url=parcel_availabe_url,params={'country_code' : order.partner_shipping_id.country_id.code, 'weight' : total_weight},headers=headers)
                if 'services' in json.loads(avail_result.text):
                    services_dict = json.loads(avail_result.text).get('services').get('service')
                    
                    if services_dict:
                        for service in services_dict:
                            if service.get('name') in ['Large Letter', 'Small Letter']:
                                service_available = True
                                service_code = service.get('code')
                                
                api_url = "https://digitalapi.auspost.com.au/postage/letter/domestic/calculate.json"
            _logger.info("Service Code ===  %s .", service_code, exc_info=True)
            params.update({
                           'weight':total_weight,
                           'service_code': service_code
                           })
        
            if api_url and params and headers and service_code and service_available:
                result = requests.get(url=api_url,params=params,headers=headers)
                result = json.loads(result.text)
                
            else:
                return {'success': False,
                    'price': 0.0,
                    'error_message': 'Delivery not available within this state!',
                    'warning_message': False}
        
        if result.get('error'):
            return {'success': False,
                    'price': 0.0,
                    'error_message': _('Error:\n%s') % result['error']['errorMessage'],
                    'warning_message': False}
        else:
            if order.currency_id.name == 'AUD':
                price = float(result['postage_result']['total_cost']) * no_of_parcels
            else:
                price = float(result['postage_result']['total_cost']) * no_of_parcels
                quote_currency = ResCurrency.search([('name', '=', 'AUD')], limit=1)
                price = quote_currency._convert(
                    price, order.currency_id, order.company_id,fields.Date.today())
            return {'success': True,
                    'price': price,
                    'error_message': False,
                    'warning_message': False}
    
    