# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

class StockPicking_LineUser(models.Model):
    _inherit = 'stock.picking'
    
    delivery_line_user = fields.Many2one('res.users',string='Delivery User')
    
    @api.multi
    def write(self,vals):
        if vals.get('location_id'):
            if 'location_id' in vals:
                location_id = self.env['stock.location'].sudo().search([('id','=',vals.get('location_id'))])
                if location_id:
                    if location_id.nso_location_id:
                        user_id = self.env['res.users'].sudo().search([('partner_id','=',location_id.nso_location_id.id)])
                        if user_id:
                            vals.update({'delivery_line_user': user_id.id})
        return super(StockPicking_LineUser, self).write(vals)
    
    @api.model
    def create(self,vals):
        if vals.get('location_id'):
            if 'location_id' in vals:
                location_id = self.env['stock.location'].sudo().search([('id','=',vals.get('location_id'))])
                if location_id:
                    if location_id.nso_location_id:
                        user_id = self.env['res.users'].sudo().search([('partner_id','=',location_id.nso_location_id.id)])
                        if user_id:
                            vals.update({'delivery_line_user': user_id.id})
        return super(StockPicking_LineUser, self).create(vals)
    

