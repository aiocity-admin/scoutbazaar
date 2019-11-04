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

from odoo import models,fields,_,api
ADDRESS_FIELDS = ('street', 'street2', 'zip', 'city', 'state_id', 'country_id','territories_id')

class HKResPartner(models.Model):
    
    _inherit = 'res.partner'
    
    territories_id = fields.Many2one('res.partner.territories', string="Territories")
    name_building = fields.Char('Name of Building')
    
    @api.model
    def _address_fields(self):
        """Returns the list of address fields that are synced from the parent."""
        return list(ADDRESS_FIELDS)
    
class HKPartnerTerritories(models.Model):
    
    _name = 'res.partner.territories'
    
    name = fields.Char(string="Name")
    country_id = fields.Many2one('res.country', string="Country")
    
