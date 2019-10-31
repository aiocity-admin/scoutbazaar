# -*- coding: utf-8 -*-

from odoo import fields,models,api,_

class scoutstock(models.Model):

	_name="scout.stock"
	_rec_name="country_id"

	country_id = fields.Many2one("res.country", string="Country",required=True)
	state_ids = fields.Many2many('res.country.state',string="State",domain="[('country_id', '=?', country_id)]")
	location_id = fields.Many2one("stock.location", string="Location",required=True)