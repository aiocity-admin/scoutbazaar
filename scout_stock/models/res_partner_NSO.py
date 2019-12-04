# -*- coding: utf-8 -*-
from odoo import fields,models,api,_

class respartnernso(models.Model):

    _inherit="res.partner"

    is_nso = fields.Boolean(string="IS NSO")
    
    
    
class ProductPublicCategory(models.Model):

    _inherit="product.public.category"

    code = fields.Char(string='Code')