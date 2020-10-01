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
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import pdf
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError, UserError

class StockLocation(models.Model):
    
    _inherit = 'stock.location'
    
    state_id = fields.Many2one('res.country.state',string='State',domain="[('country_id.code','=','PH')]")
    nso_location_id = fields.Many2one('res.partner', string="NSO Location",domain="[('is_nso','=',True)]")
    state_country_code = fields.Char(related='nso_location_id.country_id.code')

class JTDeliveryCarrier(models.Model):
    
    _inherit = 'delivery.carrier'
    
    country_id = fields.Many2one('res.country','Country')
    
    delivery_code = fields.Char(string = 'Delivery Code')
    
    country_code = fields.Char(string='Country Code',related='country_id.code')
    
    delivery_type = fields.Selection(selection_add=[('base_on_jt_configuration', 'GSR')])
    
    big_size_price = fields.Float('Big Product Box Price')