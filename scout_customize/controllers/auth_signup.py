# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import werkzeug

from odoo import http, _
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.addons.web_settings_dashboard.controllers.main import WebSettingsDashboard as Dashboard
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

_logger = logging.getLogger(__name__)


class AuthSignup(AuthSignupHome):
    def do_signup(self, qcontext):
            """ Shared helper that creates a res.partner out of a token """
            if qcontext.get('special_offer_email'):
                if qcontext.get('special_offer_email') == 'on':
                    ids = request.env['mail.mass_mailing.list'].sudo().search([('is_user_signup_mailing_list', '=', True)])
                    value = {
                            'email':qcontext.get('login'),
                            'name':qcontext.get('name'),
#                             'country_id':category_id.country_id.id,
                    }
                    for mail_id in ids:
                        mail_id.update({'contact_ids': [(0,0,value)]})
    
            values = { key: qcontext.get(key) for key in ('login', 'name', 'password','preffered_country') }
            if not values:
                raise UserError(_("The form was not properly filled in."))
            if values.get('password') != qcontext.get('confirm_password'):
                raise UserError(_("Passwords do not match; please retype them."))
            supported_langs = [lang['code'] for lang in request.env['res.lang'].sudo().search_read([], ['code'])]
            if request.lang in supported_langs:
                values['lang'] = request.lang
            self._signup_with_values(qcontext.get('token'), values)
            request.env.cr.commit()