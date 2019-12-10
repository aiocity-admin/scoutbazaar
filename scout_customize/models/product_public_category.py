# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, UserError


class ProductPublicCategory(models.Model):
    
    _inherit='product.public.category'
    
    is_thirdparty_order = fields.Boolean(string='Is Thirdparty Order')
    thirdparty_url = fields.Char(string="Thirdparty URL")
    
