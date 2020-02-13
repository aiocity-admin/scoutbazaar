# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016-Today Geminate Consultancy Services (<http://geminatecs.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
    

