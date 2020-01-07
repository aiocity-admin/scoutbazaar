# -*- coding: utf-8 -*-
# Part of SnepTech. See LICENSE file for full copyright and licensing details.##
##################################################################################

from datetime import datetime
from odoo import http, tools, _
from odoo import api, models, fields, _
import logging
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from werkzeug.exceptions import Forbidden
from odoo.addons.http_routing.models.ir_http import slug


class CustomerPortal(CustomerPortal):
    MANDATORY_BILLING_FIELDS = ["name", "phone", "email", "street", "city", "country_id","school_list_ids","boy_scout","scout_user_rank"]
    @http.route('/my/account', type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        
        if 'school_list_ids' in self.MANDATORY_BILLING_FIELDS:
            self.MANDATORY_BILLING_FIELDS.remove("school_list_ids")
        if 'boy_scout' in self.MANDATORY_BILLING_FIELDS:
            self.MANDATORY_BILLING_FIELDS.remove("boy_scout")
        if 'scout_user_rank' in self.MANDATORY_BILLING_FIELDS:
            self.MANDATORY_BILLING_FIELDS.remove("scout_user_rank")
        
        if 'school_list_ids' not in self.OPTIONAL_BILLING_FIELDS:
                self.OPTIONAL_BILLING_FIELDS.append('school_list_ids')
        if 'boy_scout' not in self.OPTIONAL_BILLING_FIELDS:
                self.OPTIONAL_BILLING_FIELDS.append('boy_scout')
        if 'scout_user_rank' not in CustomerPortal.OPTIONAL_BILLING_FIELDS:
                self.OPTIONAL_BILLING_FIELDS.append('scout_user_rank')
        
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update({
            'error': {},
            'error_message': [],
        })

        if post:
            error, error_message = self.details_form_validate(post)
            
            values.update({'error': error, 'error_message': error_message})
            values.update(post)

            if not error:
                values = {key: post[key] for key in self.MANDATORY_BILLING_FIELDS}
                values.update({key: post[key] for key in self.OPTIONAL_BILLING_FIELDS if key in post})
                values.update({'zip': values.pop('zipcode', '')})
                values.update({'school_list_ids':[(6,0, list(map(int,request.httprequest.form.getlist('school_list_ids'))))]})
                partner.sudo().write(values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])
        school_ids = request.env['school.list'].sudo().search([])
        select_school_ids = partner.school_list_ids.ids
        select_boy_scout = partner.boy_scout
        partner_scout_user_rank = partner.scout_user_rank

        values.update({
            'partner': partner,
            'countries':countries,
            'states': states,
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'redirect': redirect,
            'page_name': 'my_details',
            'school_ids': school_ids,
            'select_school_ids':select_school_ids,
            'select_boy_scout':select_boy_scout,
            'partner_scout_user_rank':partner_scout_user_rank,
        })
        response = request.render("portal.portal_my_details", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response
    
    def details_form_validate(self, data):
        res = super(CustomerPortal,self).details_form_validate(data)
        
        if 'school_list_ids' not in CustomerPortal.OPTIONAL_BILLING_FIELDS:
                CustomerPortal.OPTIONAL_BILLING_FIELDS.append('school_list_ids')
        if 'boy_scout' not in CustomerPortal.OPTIONAL_BILLING_FIELDS:
                CustomerPortal.OPTIONAL_BILLING_FIELDS.append('boy_scout')
        if 'scout_user_rank' not in CustomerPortal.OPTIONAL_BILLING_FIELDS:
                CustomerPortal.OPTIONAL_BILLING_FIELDS.append('scout_user_rank')
        
        if 'school_list_ids' in CustomerPortal.MANDATORY_BILLING_FIELDS:
            CustomerPortal.MANDATORY_BILLING_FIELDS.remove("school_list_ids")
        if 'boy_scout' in CustomerPortal.MANDATORY_BILLING_FIELDS:
            CustomerPortal.MANDATORY_BILLING_FIELDS.remove("boy_scout")
        if 'scout_user_rank' in CustomerPortal.MANDATORY_BILLING_FIELDS:
            CustomerPortal.MANDATORY_BILLING_FIELDS.remove("scout_user_rank")
        
        user_has = request.env.user.has_group('base.user_admin')
        user_rank = data.get('scout_user_rank')
        scout_list = ['den_master','scout_master','patrol_leader','troop_leader']
        if not user_has:
            if user_rank in scout_list:
                res[0]['scout_user_rank'] = 'error'
                res[1].append(_('Only Administrator can set Troop Leader,Patrol Leader,Scout Master,Den Master'))
        return res