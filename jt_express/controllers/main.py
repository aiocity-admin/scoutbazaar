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
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError
from odoo.osv import expression

class CustomerPortalJTExress(CustomerPortal):
    
    def details_form_validate(self, data):
        country_id = data.get('country_id')
#         country_id = request.env.user.company_id
        country = request.env['res.country'].browse(int(country_id))
        if country:
            if country.code == 'PH':
                if 'city' in data:
                    data.pop('city')
                if 'city' in CustomerPortal.MANDATORY_BILLING_FIELDS:
                    CustomerPortal.MANDATORY_BILLING_FIELDS.remove("city")
                 
                if 'city_id' not in CustomerPortal.MANDATORY_BILLING_FIELDS:
                    CustomerPortal.MANDATORY_BILLING_FIELDS.append("city_id")
                     
                if 'district_id' not in CustomerPortal.MANDATORY_BILLING_FIELDS:
                    CustomerPortal.MANDATORY_BILLING_FIELDS.append("district_id")
                     
                if 'town_id' not in CustomerPortal.MANDATORY_BILLING_FIELDS:
                    CustomerPortal.MANDATORY_BILLING_FIELDS.append("town_id")
            else:
                if 'city_id' in data:
                    data.pop('city_id')
                if 'district_id' in data:
                    data.pop('district_id')
                if 'town_id' in data:
                    data.pop('town_id')
                if 'city' not in CustomerPortal.MANDATORY_BILLING_FIELDS:
                    CustomerPortal.MANDATORY_BILLING_FIELDS.append("city")
                     
                if 'city_id' in CustomerPortal.MANDATORY_BILLING_FIELDS:
                    CustomerPortal.MANDATORY_BILLING_FIELDS.remove("city_id")
                     
                if 'district_id' in CustomerPortal.MANDATORY_BILLING_FIELDS:
                    CustomerPortal.MANDATORY_BILLING_FIELDS.remove("district_id")
                     
                if 'town_id' in CustomerPortal.MANDATORY_BILLING_FIELDS:
                    CustomerPortal.MANDATORY_BILLING_FIELDS.remove("town_id")
        return super(CustomerPortalJTExress,self).details_form_validate(data)
    
    @http.route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        res = super(CustomerPortalJTExress, self).account(redirect, **post)
        town_ids = False
        district_ids = False
        ph_city_ids = False
        town_ids = request.env['res.partner.town'].sudo().search([], order="name ASC")
        district_ids = request.env['res.partner.district'].sudo().search([], order="name ASC")
        ph_city_ids = request.env['res.partner.city'].sudo().search([], order="name ASC")
        res.qcontext.update({
                'town_id':town_ids,
                'district_id':district_ids,
                'city_id':ph_city_ids,
            })
        return res
    
    @http.route('/ph/country_infos', type='json', auth="public", website=True)
    def ph_country_infos(self, country):
        country_id = request.env['res.country'].browse(int(country))
        if country_id.code == 'PH':
            return True
        else:
            return False
    
class WebsiteSaleJTExress(WebsiteSale):
    
    def values_postprocess(self, order, mode, values, errors, error_msg):
        res = super(WebsiteSaleJTExress, self).values_postprocess(order, mode, values, errors, error_msg)
        res[0].update({
                        'town_id':values.get('town_id') if values.get('town_id') else False,
                        'district_id':values.get('district_id') if values.get('district_id') else False,
                        'city_id':values.get('city_id') if values.get('city_id') else False
                     })
        return res
    
    def _get_mandatory_billing_fields(self):
        if request.context.get('address_country'):
            country = request.env['res.country']
            country = country.browse(int(request.context.get('address_country')))
            if country.code == 'PH':
                return ["name", "street", "country_id","town_id","district_id","city_id","zip"]
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
            else:
                return ["name", "street", "city", "country_id","zip"]
        else:
            return ["name", "street", "city", "country_id","zip"]
    
    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True)
    def address(self, **kw):
        res = super(WebsiteSaleJTExress, self).address( **kw)
        town_ids = False
        district_ids = False
        ph_city_ids = False
        town_ids = request.env['res.partner.town'].sudo().search([], order="name ASC")
        district_ids = request.env['res.partner.district'].sudo().search([], order="name ASC")
        ph_city_ids = request.env['res.partner.city'].sudo().search([], order="name ASC")
        res.qcontext.update({
                'town_id':town_ids,
                'district_id':district_ids,
                'city_id':ph_city_ids,
            })
        return res
    
    def checkout_form_validate(self, mode, all_form_values, data):
        
        address_country = data.get('country_id')
        request.context = dict(request.context, address_country=address_country)
        return super(WebsiteSaleJTExress,self).checkout_form_validate(mode,all_form_values,data)
    
    @http.route(['/shop/country_infos/<model("res.country"):country>'], type='json', auth="public", methods=['POST'], website=True)
    def country_infos(self, country, mode, **kw):
        if not country.code == 'PH':
            return dict(
                fields=country.get_address_fields(),
                states=[(st.id, st.name, st.code) for st in country.get_website_sale_states(mode=mode)],
                phone_code=country.phone_code
            )
        else:
            return False
        
    @http.route('/filter/ph_servicable_area', type='json', auth="public", website=True)
    def filter_servicable_area(self, city_id):
        value = {}
        district_list = []
        town_list = []
        if city_id:
            servicable_area = request.env['jt.servicable.areas'].sudo().search([('city_id','=',int(city_id))])
            for ids in servicable_area:
                if not [ids.district_id.id,ids.district_id.name] in district_list:
                    district_list.append([ids.district_id.id,ids.district_id.name])

                if not [ids.town_id.id,ids.town_id.name] in town_list:
                    town_list.append([ids.town_id.id,ids.town_id.name])
                    
            if district_list and town_list:
                return district_list,town_list
                
            else:
                return False
        else:
            return False
    
    @http.route('/filter/ph_servicable_area/district', type='json', auth="public", website=True)
    def filter_servicable_area_district(self, district_id):
        value = {}
        town_list = []
        if district_id:
            servicable_area = request.env['jt.servicable.areas'].sudo().search([('district_id','=',int(district_id))])
            for ids in servicable_area:
                if not [ids.town_id.id,ids.town_id.name] in town_list:
                    town_list.append([ids.town_id.id,ids.town_id.name])
                    
            if town_list:
                return town_list
                
            else:
                return False
        else:
            return False