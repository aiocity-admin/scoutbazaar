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


class PartnerDistrict(models.Model):
    
    
    _name = "res.partner.district"
    
    
    name= fields.Char(string='Name')
    
    country_id = fields.Many2one('res.country',string="Country")
    
    
class PartnerCity(models.Model):
    
    
    _name = "res.partner.city"
    
    
    name= fields.Char(string='Name')
    
    country_id = fields.Many2one('res.country',string="Country")
    
    
class PartnerTown(models.Model):
    
    
    _name = "res.partner.town"
    
    
    name= fields.Char(string='Name')
    
    country_id = fields.Many2one('res.country',string="Country")
    
    
# class PartnerTerritories(models.Model):
#     
#     _name = 'res.partner.territories'
#     
#     name = fields.Char(string="Name")
#     
#     country_id = fields.Many2one('res.country', string="Country")
    
    
class ServicableAreas(models.Model):
    
    _name = "jt.servicable.areas"
    
    
    town_id = fields.Many2one('res.partner.town',string='Barangay')
    district_id = fields.Many2one('res.partner.district',string='City / Municipality')
    city_id = fields.Many2one('res.partner.city',string='Province')
    state_id = fields.Many2one('res.country.state',string="State",domain="[('country_id','=','PH')]")