# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, UserError

class mass_mailingme(models.Model):
    
    _inherit='mail.mass_mailing.list'
    
    is_user_signup_mailing_list = fields.Boolean('Is Signup User Mailing List', default=False)