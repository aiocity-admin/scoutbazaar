# -*- coding: utf-8 -*-
###############################################################################
#
#   Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#   Copyright (C) 2016-today Geminate Consultancy Services (<http://geminatecs.com>).
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################


from odoo import fields,models,_,api


class JTShippingRates(models.Model):
    
    
    _name = 'jt.shipping.rates'
    
    
    min_weight = fields.Float('Minimum Weight')
    max_weight = fields.Float('Maximum Weight')
    state_id = fields.Many2one('res.country.state',string="State",domain="[('country_id','=','PH')]")
    origin_id = fields.Many2one('res.country.state',string="Origin",domain="[('country_id','=','PH')]")
    rate = fields.Float('Rate')
    name = fields.Char(string = 'Name',compute="_compute_name")
    
    
    @api.multi
    @api.depends('state_id','min_weight','max_weight')
    def _compute_name(self):
        for ship_id in self:
            if ship_id.state_id and ship_id.origin_id:
                ship_id.name = ship_id.origin_id.name + '-' + ship_id.state_id.name + '(' + str(ship_id.min_weight) + '-' +  str(ship_id.max_weight) + ')'
    
# class JTBoxCost(models.Model):
#     
#     
#     _name = 'jt.box.cost'
#     
#     
#     box_type = fields.Selection([
#                                  ('ex_small','Extra Small'),
#                                  ('small','Small'),
#                                  ('large','Large'),
#                                  ('ex_large','Extra Large')
#                                  ], string="Box Type")
#     
#     
#     min_weight = fields.Float(string='Minimum Weight')
#     
#     max_weight = fields.Float(string='Maximum Weight')
#     
#     price = fields.Float(string='Price')
#     
#     name = fields.Char(string="Name",compute= '_compute_name')
    
    
    