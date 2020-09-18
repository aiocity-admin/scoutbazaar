# -*- coding: utf-8 -*-
from odoo import http
#from openerp import http

class GlobalShippingRate(http.Controller):
    @http.route('/global_shipping_rate/global_shipping_rate/', auth='public', website=True)
    def index(self, **kw):
        return "Hello, world"
        # ShippingRates = http.request.env['shipping_rates']
        # return http.request.render('shipping_rates_listing', {
        #     'shipping_rates': ShippingRates.search([])
        # })
    
    @http.route('/global_shipping_rate/shipping_rate/', auth='public', website=True)
    def get_rate_card(self, **kw):
        ShippingRates = http.request.env['shipping_rates']
        show_rate_card = False
        error_msg = 'No Country selected'
        source_country = 'India'
        destination_country = ''
        package_weight = '0-250gm'

        if(source_country==''):
            show_rate_card = False
            error_msg = 'Source Country not selected'
            values = {
                'show_rate_card':show_rate_card,
                'error_msg':error_msg,
            }
            return http.request.render('Global_Shipping_Rate.displaiy_rate_card', values)
        if(destination_country!=''):
            show_rate_card = False
            error_msg = 'Destination Country not available'
            values = {
                'show_rate_card':show_rate_card,
                'error_msg':error_msg,
            }
            return http.request.render('Global_Shipping_Rate.displaiy_rate_card', values)
            
        if(source_country ==  destination_country):
            show_rate_card = False
            error_msg = 'Source and Destination Country are same'
            values = {
                'show_rate_card':show_rate_card,
                'error_msg':error_msg,
            }
            return http.request.render('Global_Shipping_Rate.displaiy_rate_card', values)
        

        show_rate_card = True
        values = {
            'show_rate_card':show_rate_card,
            'shipping_rates':ShippingRates.search([]),
            'source_country' : source_country,
            'destination_country' : destination_country,
            'package_weight' : package_weight
        }
        return http.request.render('Global_Shipping_Rate.displaiy_rate_card', values)


    @http.route('/global_shipping_rate/global_shipping_rate/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('global_shipping_rate.listing', {
            'root': '/global_shipping_rate/global_shipping_rate',
            'objects': http.request.env['global_shipping_rate.global_shipping_rate'].search([]),
        })

    @http.route('/global_shipping_rate/global_shipping_rate/objects/<model("global_shipping_rate.global_shipping_rate"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('global_shipping_rate.object', {
            'object': obj
        })

