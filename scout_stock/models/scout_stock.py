# -*- coding: utf-8 -*-
from odoo import fields,models,api,_

class ScoutStock(models.Model):

	_name="scout.stock"
	_rec_name="country_id"
	
	country_id = fields.Many2one("res.country", string="Country",required=True)
	state_ids = fields.Many2many('res.country.state',string="State",domain="[('country_id', '=?', country_id)]")
	location_id = fields.Many2one("stock.location", string="Location", domain="[('is_store_nso','=',True)]")
	
class NSOlocation(models.Model):
   
    _inherit="stock.location"
    
    is_store_nso = fields.Boolean(string="Is Store NSO")
    nso_location_id = fields.Many2one('res.partner', string="NSO Location",domain="[('is_nso','=',True)]")