
from odoo import fields,models,_,api

class ShippingRates(models.Model):

    _name = 'shipping_rates'  
    _description = 'Shipping rate contains all data related to shipping from source to destination'
     
    source_country = fields.Many2one('res.country', string='Source Country')
    destination_country = fields.Many2one('res.country', string='Destination Country')
    delivery_carrier = fields.Char(string='Delivery Carrier', required=True)
    min_weight = fields.Float(string='Minimum Weight', required=True)
    max_weight = fields.Float(string='Maximum Weight', required=True)
    is_active = fields.Boolean(default=False, string='Covid status / service available or not')
    rate = fields.Float('Rate', required=True)
    name = fields.Char(string='Name', compute='_compute_name')
    
    @api.depends('name')
    def _compute_name(self):
        for ship_rate in self:
                self.name = str(self.source_country.name) + '-' + str(self.destination_country.name) + '(' +  str(self.min_weight) + '-' +  str(self.max_weight) + ')gm'
    
