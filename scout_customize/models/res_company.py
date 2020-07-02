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
    delivery_product_image = fields.Binary('Shipping Products Image')


    partner1 = fields.Binary(string="Partner1")
    partner2 = fields.Binary(string="Partner2")
    partner3 = fields.Binary(string="Partner3")
    partner4 = fields.Binary(string="Partner4")
    partner5 = fields.Binary(string="Partner5")
    partner6 = fields.Binary(string="Partner6")

    website_logo = fields.Binary(string="Logo")
    website_email = fields.Char(string='Website Email')
    website_phone = fields.Char(string='Website Phone')
    scout_website = fields.Char(string='Website')