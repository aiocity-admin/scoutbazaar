# -*- coding: utf-8 -*-
from odoo import http
#from openerp import http

class GlobalShippingRate(http.Controller):

    @http.route('/global_shipping_rate/gbs_rate_card/', auth='public', website=True)
    def get_rate_card(self, **kw):
        ShippingRates = http.request.env['shipping_rates']
        show_rate_card = False
        error_msg = 'No Country selected'
        source_country = 'India'
        destination_country = ''
        min_weight = '0-250gm'
        max_weight = '0-250gm'

        if(source_country==''):
            show_rate_card = False
            error_msg = 'Source Country not selected'
            values = {
                'show_rate_card':show_rate_card,
                'error_msg':error_msg,
            }
            return http.request.render('global_shipping_rate.displaiy_rate_card', values)
        if(destination_country!=''):
            show_rate_card = False
            error_msg = 'Destination Country not available'
            values = {
                'show_rate_card':show_rate_card,
                'error_msg':error_msg,
            }
            return http.request.render('global_shipping_rate.displaiy_rate_card', values)
            
        if(source_country ==  destination_country):
            show_rate_card = False
            error_msg = 'Source and Destination Country are same'
            values = {
                'show_rate_card':show_rate_card,
                'error_msg':error_msg,
            }
            return http.request.render('global_shipping_rate.displaiy_rate_card', values)
        
        show_rate_card = True
        values = {
            'show_rate_card':show_rate_card,
            'shipping_rates':ShippingRates.search([]),
            'source_country' : source_country,
            'destination_country' : destination_country,
            'min_weight' : min_weight,
            'max_weight' : max_weight
        }
        return http.request.render('global_shipping_rate.displaiy_rate_card', values)

