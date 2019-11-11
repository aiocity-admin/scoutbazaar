

from odoo import api, models, fields, _

class DeliveryLineTrack(models.Model):
    
    
    
    _name = 'delivery.line.track'
    
    
    order_id = fields.Many2one('sale.order',string="Order")
    
    carrier_id = fields.Many2one('delivery.carrier',string="Carrier")
    
    country_id = fields.Many2one('res.country',string="Country")
    
    delivery_price = fields.Float('Delivery Price')
    
    is_vendor_track = fields.Boolean(string="Is a Vendor track")
    
    