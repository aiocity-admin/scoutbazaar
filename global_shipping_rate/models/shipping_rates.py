
from odoo import fields,models,_,api
from odoo.exceptions import UserError
from odoo.tools import pdf
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError, UserError

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