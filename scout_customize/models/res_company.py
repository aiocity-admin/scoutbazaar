# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, UserError


class ResCompany(models.Model):
    
    
    _inherit="res.company"
    
    
    
    shipping_policy = fields.Html(string='Shipping Policy')
    refund_policy = fields.Html(string='Refund Policy')
    term_of_use = fields.Html(string='Term of use')
    privacy = fields.Html(string='Privacy Policy')