
from odoo import fields,models,_,api

class GBShippingRates(models.Model):

    _name = 'gb.shipping.rates'
    _description = 'Shipping rate contains all data related to shipping from source to destination'
    
    source_country = fields.Many2one('res.country.state',string="Source Country",domain="[('country_code','=','PH')]")
    destination_country = fields.Many2one('res.country.state',string="Destination Country",domain="[('country_code','=','PH')]")
    rate = fields.Float('Rate', required=True)
    name = fields.Char(string = 'Name',compute="_compute_name")
    
    
    @api.multi
    @api.depends('source_country','destination_country','max_weight')
    def _compute_name(self):
        for ship_id in self:
            if ship_id.state_id and ship_id.origin_id:
                ship_id.name = ship_id.origin_id.name + '-' + ship_id.state_id.name + '(' + str(ship_id.min_weight) + '-' +  str(ship_id.max_weight) + ')'
    
