# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _


class ShProductTemplate(models.Model):
    _inherit = 'product.template'
    
    sh_increment_qty = fields.Char('Minimum of Quantity',default = '1')
