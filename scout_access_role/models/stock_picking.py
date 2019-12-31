# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

class StockPicking_LineUser(models.Model):
    _inherit = 'stock.picking'
    
    delivery_line_user = fields.Many2one('res.users',string='Delivery User',compute='_compute_delivery_line_user')
    
    @api.multi
    @api.depends('location_id')
    def _compute_delivery_line_user(self):
        if self.location_id and self.location_id.nso_location_id:
            user_id = self.env['res.users'].sudo().search([('partner_id','=',self.location_id.nso_location_id.id)])
            self.delivery_line_user = user_id.id
