from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import pdf
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError, UserError

class StockLocationGSR(models.Model):
    
    _inherit = 'stock.location'
    
    state_id = fields.Many2one('res.country.state',string='State')
    nso_location_id = fields.Many2one('res.partner', string="NSO Location")
    state_country_code = fields.Char(related='nso_location_id.country_id.code')

class GSRDeliveryCarrier(models.Model):
    
    _inherit = 'delivery.carrier'
    
    country_id = fields.Many2one('res.country','Country')
    
    delivery_code = fields.Char(string = 'Delivery Code')
    
    country_code = fields.Char(string='Country Code',related='country_id.code')
    
    delivery_type = fields.Selection(selection_add=[('base_on_gsr_configuration', 'GSR')])
    
    big_size_price = fields.Float('Big Product Box Price')