# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.fields import Date

class StockReportInherit(models.Model):
    
    _inherit = 'stock.report'
    
    delivery_line_user_id = fields.Many2one('res.users',string='Delivery User',store=True)
    