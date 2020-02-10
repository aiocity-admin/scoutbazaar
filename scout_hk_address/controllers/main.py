# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016-Today Geminate Consultancy Services (<http://geminatecs.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields as odoo_fields, tools, _
from odoo import http
from odoo.http import request
from odoo.addons.scout_customize.controllers.portal import CustomerPortal
# from odoo.addons.portal.controllers.portal import CustomerPortal
# from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.jt_express.controllers.main import WebsiteSaleJTExress
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError
from odoo.osv import expression

class CustomerPortalHKCountry(CustomerPortal):
    
    def details_form_validate(self, data):
        country_id = data.get('country_id')
        country = request.env['res.country'].browse(int(country_id))
        if country:
            if country.code == 'HK':
                if 'territories_id' not in CustomerPortal.OPTIONAL_BILLING_FIELDS:
                    CustomerPortal.OPTIONAL_BILLING_FIELDS.append('territories_id')
                
                if 'street2' not in CustomerPortal.MANDATORY_BILLING_FIELDS:
                    CustomerPortal.MANDATORY_BILLING_FIELDS.append("street2")
                     
                if 'name_building' not in CustomerPortal.MANDATORY_BILLING_FIELDS:
                    CustomerPortal.MANDATORY_BILLING_FIELDS.append("name_building")
            else:
                if 'territories_id' in data:
                    data.pop('territories_id')
                if 'name_building' in data:
                    data.pop('name_building')
                if 'street2' in data:
                    data.pop('street2')
                if 'territories_id' in CustomerPortal.OPTIONAL_BILLING_FIELDS:
                    CustomerPortal.OPTIONAL_BILLING_FIELDS.remove("territories_id")
                     
                if 'street2' in CustomerPortal.MANDATORY_BILLING_FIELDS:
                    CustomerPortal.MANDATORY_BILLING_FIELDS.remove("street2")
                     
                if 'name_building' in CustomerPortal.MANDATORY_BILLING_FIELDS:
                    CustomerPortal.MANDATORY_BILLING_FIELDS.remove("name_building")
        return super(CustomerPortalHKCountry,self).details_form_validate(data)
    
# class CustomerPortalHKCountry(CustomerPortal):
    @http.route('/hk/country_infos', type='json', auth="public", website=True)
    def hk_country_infos(self, country):
        country_id = request.env['res.country'].browse(int(country))
        if country_id.code == 'HK':
            return True
        else:
            return False
     
    @http.route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        res = super(CustomerPortalHKCountry, self).account(redirect, **post)
        territories_id = False
        territories_id = request.env['res.partner.territories'].sudo().search([])
        res.qcontext.update({
                'territories_id':territories_id,
            })
        return res
    
class WebsiteSaleHK(WebsiteSaleJTExress):
    
    def _get_mandatory_billing_fields(self):
        if request.context.get('address_country'):
            country = request.env['res.country']
            country = country.browse(int(request.context.get('address_country')))
            if country.code == 'PH':
                return ["name", "street", "country_id","town_id","district_id","city_id","zip"]
            elif country.code == 'HK':
                return ["name", "street", "street2","country_id","name_building","zip", "city"]
            else:
                return ["name", "email", "street", "country_id","zip", "city"]
        else:
            return ["name", "email", "street", "country_id","zip", "city"]
    def _get_mandatory_shipping_fields(self):
        if request.context.get('address_country'):
            country = request.env['res.country']
            country = country.browse(int(request.context.get('address_country')))
            if country.code == 'PH':
                return ["name", "street", "country_id","town_id","district_id","city_id","zip"]
            elif country.code == 'HK':
                return ["name", "street", "street2","country_id","name_building","zip", "city"]
            else:
                return ["name", "street", "city", "country_id","zip"]
        else:
            return ["name", "street", "city", "country_id","zip"]
    
    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True)
    def address(self, **kw):
        res = super(WebsiteSaleHK, self).address( **kw)
        territories_id = False
        territories_id = request.env['res.partner.territories'].sudo().search([])
        res.qcontext.update({
                'territories_id':territories_id,
            })
        return res
    
    def values_postprocess(self, order, mode, values, errors, error_msg):
        res = super(WebsiteSaleHK, self).values_postprocess(order, mode, values, errors, error_msg)
        res[0].update({
                        'name_building':values.get('name_building') if values.get('name_building') else False,
                        'territories_id':values.get('territories_id') if values.get('territories_id') else False,
                     })
        return res