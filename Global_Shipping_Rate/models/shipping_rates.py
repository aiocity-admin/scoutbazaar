
from odoo import fields,models,_,api

class ShippingRates(models.Model):

    _name = 'shipping_rates'  
    _description = 'Shipping rate contains all data related to shipping from source to destination'
     
    name = fields.Char(string='Name', compute='_compute_name')
    source_country = fields.Many2one('res.country', string='Source Country')
    destination_country = fields.Many2one('res.country', string='Destination Country')
    delivery_carrier = fields.Selection(
    	[('delivery_carrier_1', 'Delivery Carrier 1'), ('delivery_carrier_2', 'Delivery Carrier 2'), ('delivery_carrier_3', 'Delivery Carrier 3'), ('delivery_carrier_4', 'Delivery Carrier 4')],
    	string='Delivery Carrier')
    package_details = fields.Selection(
    	[('0-250', '0-250gm'), ('251-500', '251-500gm'), ('501-750', '501-750gm'), ('751-1000', '751-1000gm')],
    	string='Package weight')
    is_active = fields.Boolean(default=False, string='Covid status / service available or not')
    rate = fields.Float('Rate', required=True)
    
    @api.depends('name')
    def _compute_name(self):
        for ship_rate in self:
            if self.source_country and self.destination_country:
                self.name = str(self.source_country.name) + '-' + str(self.destination_country.name) + '(' +  str(self.package_details) + ')'
    
